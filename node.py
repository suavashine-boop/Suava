import requests
import json

class SuavaNode:
    def __init__(self, peers=None):
        # A list of other computers we are connected to
        self.peers = peers if peers else []

    def add_peer(self, peer_url):
        if peer_url not in self.peers:
            self.peers.append(peer_url)
            print(f"Connected to new peer: {peer_url}")

    def sync_blockchain(self, my_url):
        """Asks all connected peers for their latest blockchain data"""
        for peer in self.peers:
            try:
                print(f"Requesting blockchain from {peer}...")
                response = requests.get(f"{peer}/chain")
                if response.status_code == 200:
                    data = response.json()
                    print(f"Successfully received {len(data['chain'])} blocks from {peer}!")
                    # (In a full app, we would validate and replace our chain here)
                else:
                    print(f"Failed to sync with {peer}")
            except Exception as e:
                print(f"Could not reach {peer}. Error: {e}")