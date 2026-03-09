
from src.gui import App

from utils.binary_search import binary_search

facilities = [
    {"facility_id": 101, "name": "Hospital A"},
    {"facility_id": 102, "name": "School B"},
    {"facility_id": 103, "name": "Evac Center C"}
]

index = binary_search(facilities, 102, "facility_id")

print("Binary Search Result Index:", index)

def main():
    app = App()
    
    app.mainloop()

if __name__ == "__main__":
    main() 