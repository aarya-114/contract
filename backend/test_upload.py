import fitz

# Test with your numbered.pdf
doc = fitz.open("/Users/aaryapatil/Desktop/contractsense/backend/numbered.pdf")

# Try searching for a phrase you know is in the contract
page = doc[3]  # Page 4 (0-indexed)
results = page.search_for("Definition of terms")

print(f"Found {len(results)} matches")
for r in results:
    print(f"  Coordinates: {r}")