import unittest
from src.models import Property
from src.analyzer import PropertyAnalyzer

class TestAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = PropertyAnalyzer()

    def test_analyze_investment_potential(self):
        props = [
            Property(id="1", title="Nice House", address="A place", price=120000, url="", description="Just a normal house"),
            Property(id="2", title="Dump", address="B place", price=40000, url="", description="Needs full modernisation and refurbishment. Cash buyers only."),
            Property(id="3", title="Flat", address="C place", price=90000, url="", description="Modern flat, ready to move in. Leasehold.")
        ]
        
        analyzed = self.analyzer.analyze(props)
        
        # Prop 2 should be first (Cheap + Keywords)
        self.assertEqual(analyzed[0].id, "2")
        self.assertTrue(analyzed[0].investment_score > 5)
        
        # Prop 3 should be penalized (Leasehold)
        self.assertTrue(analyzed[-1].investment_score < analyzed[1].investment_score)
        self.assertIn("Leasehold", props[2].description)

    def test_distressed_priority(self):
        """Test that unlivable/auction properties get massive boosts"""
        props = [
            Property(id="1", title="Normal Reno", address="A", price=80000, url="", description="Needs modernization."),
            Property(id="2", title="Fire Damaged", address="B", price=80000, url="", description="Fire damage, unlivable condition. Cash buyers."),
            Property(id="3", title="Auction", address="C", price=80000, url="", description="For sale by public auction. Eviction history.")
        ]
        
        analyzed = self.analyzer.analyze(props)
        
        # Fire damaged (Prop 2) and Auction (Prop 3) should be top, significantly higher than Normal Reno (Prop 1)
        self.assertTrue(analyzed[0].id in ["2", "3"])
        self.assertTrue(analyzed[1].id in ["2", "3"])
        self.assertEqual(analyzed[-1].id, "1")
        
        # Check scores are actually boosted
        # Normal reno: ~1 (price) + 1.5 (keyword) = 2.5
        # Distressed: ~1 (price) + 3 (boost keyword) + 1.5 (cash buyers etc) = > 5
        self.assertTrue(analyzed[0].investment_score > analyzed[-1].investment_score + 2)

if __name__ == '__main__':
    unittest.main()
