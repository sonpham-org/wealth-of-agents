"""
Test suite for Market Engine and Limit Order Book.
"""

import pytest
from core.market import LimitOrderBook, MarketEngine, Order, Trade


class TestLimitOrderBook:
    """Test the Limit Order Book implementation."""
    
    def test_add_bid(self):
        """Test adding a bid order."""
        lob = LimitOrderBook("grain")
        order_id = lob.add_bid("agent_001", 10.0, 5.0)
        
        assert order_id == 1
        assert len(lob.bids) == 1
        assert lob.get_best_bid().get_display_price() == 10.0
    
    def test_add_ask(self):
        """Test adding an ask order."""
        lob = LimitOrderBook("grain")
        order_id = lob.add_ask("agent_002", 12.0, 3.0)
        
        assert order_id == 1
        assert len(lob.asks) == 1
        assert lob.get_best_ask().get_display_price() == 12.0
    
    def test_bid_sorting(self):
        """Test that bids are sorted by price (highest first)."""
        lob = LimitOrderBook("grain")
        
        lob.add_bid("agent_001", 10.0, 1.0)
        lob.add_bid("agent_002", 12.0, 1.0)
        lob.add_bid("agent_003", 11.0, 1.0)
        
        assert lob.get_best_bid().get_display_price() == 12.0
    
    def test_ask_sorting(self):
        """Test that asks are sorted by price (lowest first)."""
        lob = LimitOrderBook("grain")
        
        lob.add_ask("agent_001", 10.0, 1.0)
        lob.add_ask("agent_002", 8.0, 1.0)
        lob.add_ask("agent_003", 9.0, 1.0)
        
        assert lob.get_best_ask().get_display_price() == 8.0
    
    def test_spread(self):
        """Test bid-ask spread calculation."""
        lob = LimitOrderBook("grain")
        
        lob.add_bid("agent_001", 10.0, 1.0)
        lob.add_ask("agent_002", 12.0, 1.0)
        
        spread = lob.get_spread()
        assert spread == (10.0, 12.0)
    
    def test_no_match_wide_spread(self):
        """Test that orders don't match when spread is wide."""
        lob = LimitOrderBook("grain")
        
        lob.add_bid("agent_001", 10.0, 1.0)
        lob.add_ask("agent_002", 15.0, 1.0)
        
        trades = lob.match_orders()
        assert len(trades) == 0
    
    def test_match_crossing_orders(self):
        """Test matching when bid >= ask."""
        lob = LimitOrderBook("grain")
        
        lob.add_ask("agent_001", 10.0, 2.0)
        lob.add_bid("agent_002", 12.0, 1.0)
        
        trades = lob.match_orders()
        
        assert len(trades) == 1
        assert trades[0].buyer_id == "agent_002"
        assert trades[0].seller_id == "agent_001"
        assert trades[0].quantity == 1.0
        # Price should be ask price (arrived first)
        assert trades[0].price == 10.0
    
    def test_partial_fill(self):
        """Test partial order fills."""
        lob = LimitOrderBook("grain")
        
        lob.add_ask("agent_001", 10.0, 5.0)
        lob.add_bid("agent_002", 12.0, 2.0)
        
        trades = lob.match_orders()
        
        assert len(trades) == 1
        assert trades[0].quantity == 2.0
        
        # Ask should have 3 units remaining
        assert lob.get_best_ask().quantity == 3.0
        # Bid should be fully filled
        assert len(lob.bids) == 0
    
    def test_multiple_matches(self):
        """Test multiple orders matching in sequence."""
        lob = LimitOrderBook("grain")
        
        lob.add_ask("agent_001", 10.0, 1.0)
        lob.add_ask("agent_002", 11.0, 1.0)
        lob.add_bid("agent_003", 12.0, 2.0)
        
        trades = lob.match_orders()
        
        assert len(trades) == 2
        assert trades[0].price == 10.0
        assert trades[1].price == 11.0
    
    def test_cancel_order(self):
        """Test order cancellation."""
        lob = LimitOrderBook("grain")
        
        order_id = lob.add_bid("agent_001", 10.0, 1.0)
        assert len(lob.bids) == 1
        
        success = lob.cancel_order(order_id)
        assert success
        assert len(lob.bids) == 0
    
    def test_market_stats(self):
        """Test market statistics generation."""
        lob = LimitOrderBook("grain")
        
        lob.add_bid("agent_001", 10.0, 1.0)
        lob.add_ask("agent_002", 12.0, 1.0)
        
        stats = lob.get_market_stats()
        
        assert stats['commodity'] == 'grain'
        assert stats['best_bid'] == 10.0
        assert stats['best_ask'] == 12.0
        assert stats['spread'] == 2.0
        assert stats['num_bids'] == 1
        assert stats['num_asks'] == 1


class TestMarketEngine:
    """Test the Market Engine."""
    
    def test_initialization(self):
        """Test market engine initialization."""
        commodities = ["grain", "iron", "wood"]
        engine = MarketEngine(commodities)
        
        assert len(engine.order_books) == 3
        assert "grain" in engine.order_books
    
    def test_submit_order(self):
        """Test submitting orders to market."""
        engine = MarketEngine(["grain"])
        
        order_id = engine.submit_order("grain", "agent_001", True, 10.0, 1.0)
        assert order_id == 1
    
    def test_match_all_markets(self):
        """Test matching across multiple markets."""
        engine = MarketEngine(["grain", "iron"])
        
        # Grain market
        engine.submit_order("grain", "agent_001", False, 10.0, 1.0)
        engine.submit_order("grain", "agent_002", True, 11.0, 1.0)
        
        # Iron market
        engine.submit_order("iron", "agent_003", False, 20.0, 1.0)
        engine.submit_order("iron", "agent_004", True, 22.0, 1.0)
        
        trades = engine.match_all_markets()
        
        assert len(trades) == 2
        assert trades[0].commodity == "grain"
        assert trades[1].commodity == "iron"
    
    def test_get_all_market_stats(self):
        """Test getting statistics for all markets."""
        engine = MarketEngine(["grain", "iron"])
        
        engine.submit_order("grain", "agent_001", True, 10.0, 1.0)
        
        stats = engine.get_all_market_stats()
        
        assert "grain" in stats
        assert "iron" in stats
        assert stats["grain"]["num_bids"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
