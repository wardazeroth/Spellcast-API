def mask(secret: str | None, show: int= 3, mask_char:str = '*')-> str:
    return (mask_char * 6) + secret[-show:]