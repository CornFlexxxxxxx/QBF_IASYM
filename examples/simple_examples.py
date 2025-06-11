#!/usr/bin/env python3
"""
Simple QBF examples using the system
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from qbf_system import QBFLogicSystem
from config import Config

def example_tautology():
    """Example: Tautology"""
    print("=== Example 1: Tautology ===")
    print("Formula: ∀x (x ∨ ¬x)")
    print("Expected: SATISFIABLE")
    
    system = QBFLogicSystem(
        jar_path=str(Config.JAR_PATH),
        llm_api_key=Config.get_api_key()
    )
    
    result = system.evaluate_qbf('x | ~x', ['x'], [('forall', 'x')])
    print(f"Result: {result['result']}")
    print(f"Time: {result['execution_time']:.4f}s")
    return result['result'] == 'SATISFIABLE'

def example_contradiction():
    """Example: Contradiction"""
    print("\n=== Example 2: Contradiction ===")
    print("Formula: ∀x (x ∧ ¬x)")
    print("Expected: UNSATISFIABLE")
    
    system = QBFLogicSystem(
        jar_path=str(Config.JAR_PATH),
        llm_api_key=Config.get_api_key()
    )
    
    result = system.evaluate_qbf('x & ~x', ['x'], [('forall', 'x')])
    print(f"Result: {result['result']}")
    print(f"Time: {result['execution_time']:.4f}s")
    return result['result'] == 'UNSATISFIABLE'

def example_existential():
    """Example: Existential"""
    print("\n=== Example 3: Existential ===")
    print("Formula: ∃x ∀y (x ∨ y)")
    print("Expected: SATISFIABLE")
    
    system = QBFLogicSystem(
        jar_path=str(Config.JAR_PATH),
        llm_api_key=Config.get_api_key()
    )
    
    result = system.evaluate_qbf('x | y', ['x', 'y'], [('exists', 'x'), ('forall', 'y')])
    print(f"Result: {result['result']}")
    print(f"Time: {result['execution_time']:.4f}s")
    return result['result'] == 'SATISFIABLE'

def example_natural_language():
    """Example: Natural language"""
    print("\n=== Example 4: Natural Language ===")
    
    if not Config.get_api_key():
        print("⚠️ No API key - skipping natural language example")
        return True
    
    system = QBFLogicSystem(
        jar_path=str(Config.JAR_PATH),
        llm_api_key=Config.get_api_key()
    )
    
    text = "Every proposition is either true or false"
    print(f"Text: '{text}'")
    
    try:
        result = system.evaluate_text(text)
        print(f"Generated QBF: {result['qbf_formula']}")
        print(f"Variables: {result['variables']}")
        print(f"Quantifiers: {result['quantifiers']}")
        print(f"Result: {result['result']}")
        return True
    except Exception as e:
        print(f"❌ Natural language example failed: {e}")
        return False

def main():
    """Run all examples"""
    print("QBF Logic System - Simple Examples")
    print("=" * 40)
    
    examples = [
        ("Tautology", example_tautology),
        ("Contradiction", example_contradiction),
        ("Existential", example_existential),
        ("Natural Language", example_natural_language)
    ]
    
    results = {}
    for name, func in examples:
        try:
            results[name] = func()
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 40)
    print("EXAMPLES SUMMARY")
    print("=" * 40)
    
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name:20} {status}")
    
    passed = sum(results.values())
    total = len(results)
    print(f"\nTotal: {passed}/{total} examples passed")

if __name__ == "__main__":
    main()