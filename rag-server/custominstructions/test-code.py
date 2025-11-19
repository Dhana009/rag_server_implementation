"""
Test code file for RAG server testing.
"""

def test_function():
    """A simple test function."""
    return "Hello, World!"

class TestClass:
    """A test class for code indexing."""
    
    def __init__(self, name: str):
        self.name = name
    
    def greet(self) -> str:
        """Return a greeting message."""
        return f"Hello, {self.name}!"

def main():
    """Main function for testing."""
    obj = TestClass("RAG Server")
    print(obj.greet())
    print(test_function())

if __name__ == "__main__":
    main()

