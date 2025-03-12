# block - a python object to be used in other apps

class block:
    def __init__(self, depth = 0, prev_hash = "0"*64) -> None:
        self.depth = depth
        self.prev_hash = prev_hash
        self.nonce = "0"
        self.tx = []
        
    def __repr__(self):
        answer = f"BLOCK {str(self.depth)}\nPREVIOUS HASH: \n"
        for i in range(8):
            answer += (self.prev_hash[i*8:i*8+8] + "\n")
        answer += f"NONCE: {str(self.nonce)}\nTRANSACTIONS:\n"
        for t in self.tx:
            answer += f"{t}\n"
        return answer