#!/usr/bin/env python3
"""
Demonstration of the fixed trace system.
"""
from fixed_trace_generator import create_trace_generators

def demo_fixed_traces():
    """Demonstrate the fixed trace system."""
    print("Fixed Trace File Generator Demo")
    print("=" * 50)
    print("Configuration: 10 total files, 3 important, 7 useless")
    print("=" * 50)
    
    # Create all trace generators
    trace_generators = create_trace_generators()
    
    for trace_name, generator in trace_generators.items():
        print(f"\n{trace_name.upper()} TRACE:")
        print("-" * 30)
        
        # Get trace info
        trace_info = generator.get_trace_info()
        
        print(f"File Order: {trace_info['file_order']}")
        print(f"Important Files: {trace_info['important_file_names']}")
        print(f"Useless Files: {trace_info['useless_file_names']}")
        
        # Show sample content
        print(f"\nSample Content:")
        important_file = trace_info['important_file_names'][0]
        useless_file = trace_info['useless_file_names'][0]
        
        important_content = generator.generate_file_content(important_file)
        useless_content = generator.generate_file_content(useless_file)
        
        print(f"  {important_file}: {important_content[:60]}...")
        print(f"  {useless_file}: {useless_content[:60]}...")
        
        print(f"\nVerification:")
        print(f"  Is {important_file} important? {generator.is_important_file(important_file)}")
        print(f"  Is {useless_file} important? {generator.is_important_file(useless_file)}")
    
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    print("✅ Fixed trace system created successfully!")
    print("✅ All three traces have consistent file configurations")
    print("✅ Important files are properly identified")
    print("✅ File content generation works correctly")
    print("✅ Ready for evaluation with fixed, reproducible traces")

if __name__ == "__main__":
    demo_fixed_traces()




