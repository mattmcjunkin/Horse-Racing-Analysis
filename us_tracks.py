from __future__ import annotations

US_TRACKS = [
    "AQU","BEL","SAR","BAQ","CD","KEE","ELP","GP","GPW","TAM","MTH","PRX","PEN","PID","LRL","PIM",
    "WO","FE","AP","HAW","FG","LAD","DED","EVD","CT","MNR","TDN","BTP","IND","HOO","OP","RP",
    "SA","DMR","LRC","GG","BM","PLN","OTP","TUP","RUI","ZIA","SUN","EMD","HST","ALB","CBY","FON",
    "PRM","LS","RET","HOU","MVR","Arap","DEL","MED","ASD","LA","SUF","MTHA","MESA","UNK"
]

def track_options() -> list[str]:
    return sorted(set(US_TRACKS))
