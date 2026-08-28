"""Quick test script to validate enhanced feature extraction."""

from physics_diagram.parser import parse

test_cases = [
    "A 20 kg suitcase is pulled using a 100 N force making an angle of 30° above the horizontal.",
    "A 12 kg crate is pushed across a floor with a force of 60 N. The coefficient of kinetic friction is 0.3.",
    "A 7 kg box is pushed up a 25° incline by a 100 N force parallel to the incline. The surface is rough with μ = 0.15.",
    "A 50 N force is applied at 45° above horizontal to a 10 kg block on a frictionless floor.",
    "A 10 kg block rests on a 45° incline. The coefficient of friction between the block and the incline is 0.2.",
]

print("=" * 80)
print("FEATURE EXTRACTION TEST")
print("=" * 80)

for i, text in enumerate(test_cases, 1):
    print(f"\n[Test {i}] {text}")
    print("-" * 80)
    
    result = parse(text)
    
    print(f"Scenario: {result.scenario_type} (confidence: {result.confidence:.2f})")
    print(f"Complete: {result.is_complete} (missing: {result.missing_required})")
    
    if result.objects:
        print(f"Objects: {len(result.objects)}")
        for obj in result.objects:
            print(f"  - {obj.label}: {obj.mass_kg} kg")
    
    if result.friction or result.mu is not None:
        print(f"Friction: {result.friction}, μ = {result.mu}")
    
    if result.applied_forces:
        print(f"Applied Forces: {len(result.applied_forces)}")
        for force in result.applied_forces:
            angle_str = f", angle={force.angle_deg}° ({force.reference_frame})" if force.angle_deg else ""
            print(f"  - {force.magnitude_n} N {force.direction}{angle_str}")
    
    if result.geometry.incline_angle_deg:
        print(f"Incline: {result.geometry.incline_angle_deg}°")
    
    print()

print("=" * 80)
print("✓ Extraction test complete. Review the output above.")
print("=" * 80)
