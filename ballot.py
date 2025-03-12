from functools import total_ordering

@total_ordering
class Ballot:
    def __init__(self, n, pid, depth) -> None:
        self.n = n
        self.pid = str(pid)
        self.depth = depth
    
    def __lt__(self, other):
        if self.depth < other.depth:
            return True
        if self.n < other.n:
            return True
        if self.n == other.n:
            if self.pid < other.pid:
                return True
        return False
    
    def __eq__(self, other):
        if self.depth != other.depth:
            return False
        if self.n != other.n:
            return False
        if self.pid != other.pid:
            return False
        return True
    
    def __repr__(self) -> str:
        return f"<{self.n},{self.pid},{self.depth}>"
    