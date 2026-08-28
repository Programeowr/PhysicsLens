"""Quick test script to demonstrate the hybrid parser flow.

Run this after starting Ollama with `ollama serve` and ensuring qwen2.5:7b is available.
"""

from physics_diagram.pipeline import solve_and_render
from pathlib import Path
import tempfile

# Test cases that demonstrate the three-tier flow
test_cases = [
    {
        "name": "Simple case (deterministic succeeds)",
        "text": "A 5kg block on a 30 degree incline",
        "expected": "Complete parse, no LLM needed"
    },
    {
        "name": "Complex case (LLM fallback needed)",
        "text": "A soccer ball is kicked at thirty-five degrees above horizontal with initial speed of 18 m/s",
        "expected": "Deterministic misses angle, LLM extracts it"
    },
    {
        "name": "Missing info (both parsers fail)",
        "text": "A block slides down a ramp",
        "expected": "Missing mass and angle, shows missing fields"
    }
]

def test_hybrid_flow():
    """Test the three-tier hybrid parsing flow."""
    print("=" * 70)
    print("HYBRID PARSER FLOW TEST")
    print("=" * 70)
    print()
    
    for i, case in enumerate(test_cases, 1):
        print(f"{i}. {case['name']}")
        print(f"   Input: '{case['text']}'")
        print(f"   Expected: {case['expected']}")
        print()
        
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
            output_path = tmp.name
        
        try:
            # Use hybrid mode (default)
            result = solve_and_render(case["text"], output_path)
            
            print(f"   Status: {result['status']}")
            print(f"   Missing: {result['missing_fields']}")
            
            if result['status'] == 'ok':
                print(f"   ✓ Successfully generated diagram")
                if result.get('force_solution'):
                    print(f"   Derived values: {list(result['force_solution'].derived_values.keys())}")
            elif result['status'] == 'needs_clarification':
                print(f"   ⚠ Incomplete parse - missing: {', '.join(result['missing_fields'])}")
            elif result['status'] == 'unsupported_scenario':
                print(f"   ⚠ Scenario not yet supported")
                
            print()
        except Exception as e:
            print(f"   ✗ Error: {e}")
            print()
        finally:
            Path(output_path).unlink(missing_ok=True)
    
    print("=" * 70)
    print()
    print("To see this in the frontend:")
    print("1. Start API: py -m uvicorn physics_diagram.api:app --host 127.0.0.1 --port 8000")
    print("2. Start frontend: npm --prefix frontend run dev")
    print("3. Try the test cases above in the UI")
    print()
    print("The missing fields will now be displayed in a styled alert box!")

if __name__ == "__main__":
    test_hybrid_flow()
