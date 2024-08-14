class ResultDto:
    def __init__(self, verdict: str, score: float, max_score: float, elapsed: int, message: str):
        self.verdict = verdict
        self.score = score
        self.max_score = max_score
        self.elapsed = elapsed # in milliseconds
        self.message = message
    
    def __str__(self):
        return f"Result : {self.verdict};{self.score};{self.max_score};{self.elapsed};{self.message}"
    
    def to_string_result(self):
        return f"{self.verdict};{self.score};{self.max_score};{self.elapsed};0;{self.message}"
    
    def __repr__(self):
        return self.__str__()

