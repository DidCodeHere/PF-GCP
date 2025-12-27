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

if __name__ == '__main__':
    unittest.main()
