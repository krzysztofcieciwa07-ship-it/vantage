import hashlib
def required_window(seed:int,elapsed_seconds:int=0)->int:
    base=100+(int(hashlib.sha256(str(seed).encode()).hexdigest()[:8],16)%41)
    penalty=max(0,elapsed_seconds-1800)//60*2
    return min(300,base+penalty)
