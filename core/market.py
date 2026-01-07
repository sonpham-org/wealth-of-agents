"""
High-Performance Limit Order Book (LOB) for MPES
Uses bisect for O(log N) insertion and matching operations.
"""

import bisect
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
from collections import defaultdict
import time


@dataclass(order=True)
class Order:
    """Represents a single order in the order book."""
    price: float
    quantity: float = field(compare=False)
    agent_id: str = field(compare=False)
    order_id: int = field(compare=False)
    timestamp: float = field(compare=False, default_factory=time.time)
    is_bid: bool = field(compare=False, default=True)
    
    def __post_init__(self):
        # For bids, we want highest price first (negative for reverse sorting)
        if self.is_bid:
            self.price = -self.price
    
    def get_display_price(self) -> float:
        """Get the actual price (accounting for bid negation)."""
        return -self.price if self.is_bid else self.price


@dataclass
class Trade:
    """Represents an executed trade."""
    buyer_id: str
    seller_id: str
    commodity: str
    price: float
    quantity: float
    timestamp: float = field(default_factory=time.time)


class LimitOrderBook:
    """
    High-performance Limit Order Book with O(log N) operations.
    
    Maintains separate sorted lists for bids and asks.
    Bids are stored as negative prices for descending order.
    """
    
    def __init__(self, commodity: str):
        self.commodity = commodity
        self.bids: List[Order] = []  # Sorted descending by price (stored as negative)
        self.asks: List[Order] = []  # Sorted ascending by price
        self.order_counter = 0
        self.trade_history: List[Trade] = []
        self.order_map: Dict[int, Order] = {}  # For O(1) order lookup
        
    def add_bid(self, agent_id: str, price: float, quantity: float) -> int:
        """Add a bid order. Returns order_id."""
        self.order_counter += 1
        order = Order(
            price=price,
            quantity=quantity,
            agent_id=agent_id,
            order_id=self.order_counter,
            is_bid=True
        )
        bisect.insort(self.bids, order)
        self.order_map[order.order_id] = order
        return order.order_id
    
    def add_ask(self, agent_id: str, price: float, quantity: float) -> int:
        """Add an ask order. Returns order_id."""
        self.order_counter += 1
        order = Order(
            price=price,
            quantity=quantity,
            agent_id=agent_id,
            order_id=self.order_counter,
            is_bid=False
        )
        bisect.insort(self.asks, order)
        self.order_map[order.order_id] = order
        return order.order_id
    
    def cancel_order(self, order_id: int) -> bool:
        """Cancel an order by ID. Returns True if successful."""
        if order_id not in self.order_map:
            return False
        
        order = self.order_map[order_id]
        order_list = self.bids if order.is_bid else self.asks
        
        try:
            order_list.remove(order)
            del self.order_map[order_id]
            return True
        except ValueError:
            return False
    
    def get_best_bid(self) -> Optional[Order]:
        """Get the highest bid (best buy price)."""
        return self.bids[0] if self.bids else None
    
    def get_best_ask(self) -> Optional[Order]:
        """Get the lowest ask (best sell price)."""
        return self.asks[0] if self.asks else None
    
    def get_spread(self) -> Optional[Tuple[float, float]]:
        """Get the bid-ask spread. Returns (best_bid, best_ask) or None."""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        
        if best_bid and best_ask:
            return (best_bid.get_display_price(), best_ask.get_display_price())
        return None
    
    def match_orders(self) -> List[Trade]:
        """
        Match crossing orders and return executed trades.
        Continues matching until no more crosses exist.
        """
        new_trades = []
        
        while self.bids and self.asks:
            best_bid = self.bids[0]
            best_ask = self.asks[0]
            
            # Check if orders cross (bid >= ask)
            if best_bid.get_display_price() < best_ask.get_display_price():
                break
            
            # Execute trade at the price of the order that arrived first
            trade_price = (
                best_ask.get_display_price() 
                if best_ask.timestamp < best_bid.timestamp 
                else best_bid.get_display_price()
            )
            
            # Match quantity (take minimum)
            trade_quantity = min(best_bid.quantity, best_ask.quantity)
            
            # Create trade record
            trade = Trade(
                buyer_id=best_bid.agent_id,
                seller_id=best_ask.agent_id,
                commodity=self.commodity,
                price=trade_price,
                quantity=trade_quantity
            )
            new_trades.append(trade)
            self.trade_history.append(trade)
            
            # Update order quantities
            best_bid.quantity -= trade_quantity
            best_ask.quantity -= trade_quantity
            
            # Remove filled orders
            if best_bid.quantity <= 0:
                self.bids.pop(0)
                del self.order_map[best_bid.order_id]
            
            if best_ask.quantity <= 0:
                self.asks.pop(0)
                del self.order_map[best_ask.order_id]
        
        return new_trades
    
    def get_order_book_depth(self, levels: int = 5) -> Dict:
        """Get order book depth for visualization."""
        return {
            'bids': [
                {
                    'price': order.get_display_price(),
                    'quantity': order.quantity,
                    'agent_id': order.agent_id
                }
                for order in self.bids[:levels]
            ],
            'asks': [
                {
                    'price': order.get_display_price(),
                    'quantity': order.quantity,
                    'agent_id': order.agent_id
                }
                for order in self.asks[:levels]
            ]
        }
    
    def get_market_stats(self) -> Dict:
        """Get market statistics for analysis."""
        spread = self.get_spread()
        recent_trades = self.trade_history[-100:] if self.trade_history else []
        
        avg_price = (
            sum(t.price for t in recent_trades) / len(recent_trades)
            if recent_trades else 0
        )
        
        return {
            'commodity': self.commodity,
            'best_bid': spread[0] if spread else None,
            'best_ask': spread[1] if spread else None,
            'spread': spread[1] - spread[0] if spread else None,
            'num_bids': len(self.bids),
            'num_asks': len(self.asks),
            'total_trades': len(self.trade_history),
            'avg_price_recent': avg_price,
            'last_trade_price': recent_trades[-1].price if recent_trades else None
        }


class MarketEngine:
    """
    Central market engine managing multiple commodity order books.
    Handles all matching and trade execution.
    """
    
    def __init__(self, commodities: List[str]):
        self.order_books: Dict[str, LimitOrderBook] = {
            commodity: LimitOrderBook(commodity)
            for commodity in commodities
        }
        self.all_trades: List[Trade] = []
    
    def submit_order(
        self, 
        commodity: str, 
        agent_id: str, 
        is_bid: bool, 
        price: float, 
        quantity: float
    ) -> int:
        """Submit an order to the appropriate order book."""
        if commodity not in self.order_books:
            raise ValueError(f"Unknown commodity: {commodity}")
        
        lob = self.order_books[commodity]
        if is_bid:
            return lob.add_bid(agent_id, price, quantity)
        else:
            return lob.add_ask(agent_id, price, quantity)
    
    def match_all_markets(self) -> List[Trade]:
        """Match orders across all commodity markets."""
        all_new_trades = []
        for lob in self.order_books.values():
            trades = lob.match_orders()
            all_new_trades.extend(trades)
            self.all_trades.extend(trades)
        return all_new_trades
    
    def get_all_market_stats(self) -> Dict[str, Dict]:
        """Get statistics for all markets."""
        return {
            commodity: lob.get_market_stats()
            for commodity, lob in self.order_books.items()
        }
    
    def get_order_book_snapshot(self) -> Dict:
        """Get full snapshot of all order books for visualization."""
        return {
            commodity: lob.get_order_book_depth(levels=10)
            for commodity, lob in self.order_books.items()
        }
    
    def cancel_order(self, commodity: str, order_id: int) -> bool:
        """Cancel a specific order."""
        if commodity not in self.order_books:
            return False
        return self.order_books[commodity].cancel_order(order_id)
