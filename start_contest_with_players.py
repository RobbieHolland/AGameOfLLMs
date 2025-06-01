#!/usr/bin/env python3

from backend.contest_engine import ContestEngine
from developers.starter_developer import Phi4Developer

def main():
    """Start contest with 2 Phi-4 developers and PrincipleEvaluator."""
    
    print("🏁 Starting Code-Writing Contest with Phi-4 AI players...")
    
    # Initialize contest engine (this will also initialize the shared Phi-4 model)
    engine = ContestEngine.get_instance()
    
    # Show shared model status
    from backend.phi4_model import get_phi4_model
    phi4_model = get_phi4_model()
    print(f"🔧 Shared Phi-4 Model: {phi4_model.get_device_info()}")
    
    # Create 2 Phi-4 developers
    print("🤖 Creating Phi-4 developers...")
    dev1 = Phi4Developer("Alice")
    dev2 = Phi4Developer("Bob")
    
    # Register developers
    print("📝 Registering developers...")
    engine.register_developer(dev1)
    engine.register_developer(dev2)
    
    # Show initial status
    print("\n💰 Initial Bank Status:")
    for name, balance in engine.bank.get_all_balances().items():
        print(f"  {name}: ${balance}")
    
    print(f"\n📚 Loaded {len(engine.problems)} problems")
    print(f"⚖️ Constitution: {engine.constitution.query()[:100]}...")
    
    # Start the contest
    print("\n🚀 Starting contest...")
    engine.run_full_contest()
    
    # Final results
    print("\n🏆 FINAL RESULTS:")
    leaderboard = engine.bank.get_leaderboard()
    for i, entry in enumerate(leaderboard, 1):
        print(f"  {i}. {entry['name']}: ${entry['balance']}")
    
    print("\n✅ Contest completed!")

if __name__ == "__main__":
    main() 