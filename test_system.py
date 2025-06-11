#!/usr/bin/env python3
"""
Test the QBF system with actual TweetyProject classes
"""

import sys
from pathlib import Path
import subprocess

sys.path.append(str(Path(__file__).parent))

def test_basic_requirements():
    """Test basic system requirements"""
    print("=== Testing Basic Requirements ===")
    
    # Check JAR exists
    jar_path = Path("org.tweetyproject.logics.qbf-1.28-with-dependencies.jar")
    if not jar_path.exists():
        print(f"❌ JAR not found: {jar_path}")
        return False
    print(f"✅ JAR found: {jar_path}")
    
    # Check Java
    try:
        result = subprocess.run(["java", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Java available")
        else:
            print("❌ Java not working")
            return False
    except FileNotFoundError:
        print("❌ Java not found")
        return False
    
    # Check config
    try:
        from config import Config
        if Config.validate_config():
            print("✅ Configuration valid")
        else:
            print("⚠️ Configuration has issues (may need .env file)")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    return True

def test_qbf_system():
    """Test the QBF system"""
    print("\n=== Testing QBF System ===")
    
    try:
        from qbf_system import QBFLogicSystem
        from config import Config
        
        system = QBFLogicSystem(
            jar_path=str(Config.JAR_PATH),
            llm_api_key=Config.get_api_key()
        )
        print("✅ QBF System initialized")
        
        # Test tautology
        result = system.evaluate_qbf('x | ~x', ['x'], [('forall', 'x')])
        if result['result'] == 'SATISFIABLE':
            print("✅ Tautology test passed")
        else:
            print(f"❌ Tautology test failed: {result['result']}")
            return False
        
        # Test contradiction
        result = system.evaluate_qbf('x & ~x', ['x'], [('forall', 'x')])
        if result['result'] == 'UNSATISFIABLE':
            print("✅ Contradiction test passed")
        else:
            print(f"❌ Contradiction test failed: {result['result']}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ QBF System test failed: {e}")
        return False

def test_ui_dependencies():
    """Test UI dependencies"""
    print("\n=== Testing UI Dependencies ===")
    
    try:
        import streamlit
        print("✅ Streamlit available")
    except ImportError:
        print("⚠️ Streamlit not installed (run: pip install streamlit)")
        return False
    
    try:
        import pandas
        print("✅ Pandas available")
    except ImportError:
        print("⚠️ Pandas not installed")
        return False
    
    return True

def main():
    """Run all tests"""
    print("QBF Logic System - Test Suite")
    print("=" * 40)
    
    tests = [
        ("Basic Requirements", test_basic_requirements),
        ("QBF System", test_qbf_system),
        ("UI Dependencies", test_ui_dependencies)
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except KeyboardInterrupt:
            print("\n⚠️ Interrupted")
            break
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 40)
    print("TEST SUMMARY")
    print("=" * 40)
    
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name:20} {status}")
    
    passed = sum(results.values())
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System ready.")
        print("\nTo launch UI: python run_ui.py")
    else:
        print(f"\n⚠️ {total - passed} tests failed.")
        print("Check the issues above before launching.")

if __name__ == "__main__":
    main()