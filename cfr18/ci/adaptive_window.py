import hashlib
def base_window(seed:int)->int:
    return 100+(int(hashlib.sha256(f"CFR18:hidden001:{seed}".encode()).hexdigest()[:8],16)%41)
def required_window(seed:int,elapsed_seconds:int=0)->int:
    base=base_window(seed); penalty=max(0,elapsed_seconds-1800)//60*2
    return min(300,base+penalty)
