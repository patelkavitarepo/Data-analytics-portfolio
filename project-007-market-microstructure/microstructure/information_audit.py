"""Case 016 pure information-content diagnostics. No source IO, fitting or tuning."""
from math import isfinite
from collections import Counter

CLASSES=(1,2,3)
BINS=tuple(i/10 for i in range(11))

def prevalence(labels):
    labels=tuple(labels)
    if any(y not in (None,)+CLASSES for y in labels):
        raise ValueError("unknown target class")
    n=len(labels); known=[y for y in labels if y is not None]
    counts={y:known.count(y) for y in CLASSES}
    return {"source_n":n,"verifiable_n":len(known),"unknown_n":n-len(known),
            "class_counts":counts,
            "class_rates":{y:counts[y]/len(known) if known else None for y in CLASSES}}

def _paired(scores,labels):
    scores=tuple(scores);labels=tuple(labels)
    if len(scores)!=len(labels):
        raise ValueError("source origins must align")
    pairs=[]
    for score,label in zip(scores,labels):
        if label not in (None,)+CLASSES:
            raise ValueError("bad label")
        if score is not None and (not isinstance(score,(int,float))
                                  or not isfinite(score) or not 0<=score<=1):
            raise ValueError("probabilities must be finite [0,1]")
        if score is not None and label is not None:
            pairs.append((float(score),int(label)))
    return pairs

def average_precision(scores,labels,positive):
    """Tie-safe noninterpolated PR average precision; undefined with no positives."""
    if positive not in (1,3):
        raise ValueError("directional class only")
    pairs=_paired(scores,labels)
    if not pairs:return None
    total=sum(y==positive for _,y in pairs)
    if not total:return None
    pairs.sort(key=lambda x:x[0],reverse=True)
    tp=0;seen=0;ap=0.
    i=0
    while i<len(pairs):
        score=pairs[i][0];j=i
        while j<len(pairs) and pairs[j][0]==score:
            j+=1
        group=pairs[i:j];n_positive=sum(y==positive for _,y in group)
        tp+=n_positive;seen+=len(group)
        ap+=(n_positive/total)*(tp/seen)
        i=j
    return ap

def calibration(scores,labels,positive):
    if positive not in (1,3):
        raise ValueError("directional class only")
    pairs=_paired(scores,labels)
    bins=[{"n":0,"probability_sum":0.,"positive":0} for _ in range(10)]
    for score,y in pairs:
        idx=min(int(score*10),9)
        b=bins[idx]
        b["n"]+=1;b["probability_sum"]+=score;b["positive"]+=int(y==positive)
    return {"n":len(pairs),
            "brier":sum((score-int(y==positive))**2 for score,y in pairs)/len(pairs)
                    if pairs else None,
            "bins":[{"left":BINS[i],"right":BINS[i+1],"n":b["n"],
                     "mean_probability":b["probability_sum"]/b["n"] if b["n"] else None,
                     "observed_frequency":b["positive"]/b["n"] if b["n"] else None}
                    for i,b in enumerate(bins)]}

def descriptive_top_fraction(scores,labels,positive,fraction):
    """Retrospective descriptive ranking, NEVER a prospective alert threshold."""
    if fraction not in (.01,.02,.05) or positive not in (1,3):
        raise ValueError("predeclared diagnostic fractions/classes only")
    pairs=_paired(scores,labels)
    if not pairs:return {"n":0,"correct":0,"precision":None,"ties_at_boundary":False}
    from math import ceil
    k=max(1,ceil(fraction*len(pairs)))
    ranked=sorted(pairs,key=lambda p:p[0],reverse=True)
    selected=ranked[:k]
    return {"n":k,"correct":sum(y==positive for _,y in selected),
            "precision":sum(y==positive for _,y in selected)/k,
            "ties_at_boundary":k<len(ranked) and ranked[k-1][0]==ranked[k][0]}
