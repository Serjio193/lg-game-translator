"""Offline quality comparison to STRICT, not a ground-truth accuracy metric."""


def polygon_area(points):
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in
                   zip(points,points[1:]+points[:1])))/2


def quad_points(line):
    q=line["source_quad"]
    return [(q[k]["x"],q[k]["y"]) for k in ("p0","p1","p2","p3")]


def quad_iou(a,b):
    """Convex polygon clipping, works for either winding and rotated boxes."""
    orientation=sum(p[0]*q[1]-q[0]*p[1] for p,q in zip(b,b[1:]+b[:1]))
    direction=1 if orientation>=0 else -1
    intersection=list(a)
    for p,q in zip(b,b[1:]+b[:1]):
        def side(x):
            return direction*((q[0]-p[0])*(x[1]-p[1])-(q[1]-p[1])*(x[0]-p[0]))
        old=intersection
        intersection=[]
        if not old:
            break
        previous=old[-1]
        sp=side(previous)
        for current in old:
            sc=side(current)
            if (sc>=0)!=(sp>=0):
                t=sp/(sp-sc)
                intersection.append((previous[0]+t*(current[0]-previous[0]),
                                     previous[1]+t*(current[1]-previous[1])))
            if sc>=0:
                intersection.append(current)
            previous,sp=current,sc
    area=polygon_area(intersection)
    union=polygon_area(a)+polygon_area(b)-area
    return area/union if union>0 else 0.0


def maximum_assignment(weights):
    """Hungarian one-to-one maximum-weight assignment with zero dummy slots."""
    n=len(weights)
    m=max((len(r) for r in weights),default=0)
    size=max(n,m)
    u,v,p,way=([0.0]*(size+1) for _ in range(4))
    p=[0]*(size+1)
    way=[0]*(size+1)
    for i in range(1,size+1):
        p[0]=i
        j0=0
        minimum=[float("inf")]*(size+1)
        used=[False]*(size+1)
        while True:
            used[j0]=True
            i0=p[j0]
            delta=float("inf")
            j1=0
            for j in range(1,size+1):
                if used[j]:
                    continue
                weight=weights[i0-1][j-1] if i0<=n and j<=m else 0.0
                cost=-weight-u[i0]-v[j]
                if cost<minimum[j]:
                    minimum[j],way[j]=cost,j0
                if minimum[j]<delta:
                    delta,j1=minimum[j],j
            for j in range(size+1):
                if used[j]:
                    u[p[j]]+=delta
                    v[j]-=delta
                else:
                    minimum[j]-=delta
            j0=j1
            if p[j0]==0:
                break
        while j0:
            j1=way[j0]
            p[j0]=p[j1]
            j0=j1
    return [(p[j]-1,j-1) for j in range(1,size+1) if 0<p[j]<=n and j<=m]


def character_distance(a,b):
    """Unicode code point Levenshtein distance, preserves punctuation and case."""
    previous=list(range(len(b)+1))
    for i,ca in enumerate(a,1):
        current=[i]
        for j,cb in enumerate(b,1):
            current.append(min(previous[j]+1,current[-1]+1,previous[j-1]+(ca!=cb)))
        previous=current
    return previous[-1]


def compare_lines(strict,fast,minimum_iou=0.5):
    weights=[[quad_iou(quad_points(a),quad_points(b)) for b in fast] for a in strict]
    # Threshold is an evaluation matching rule, never a detector parameter.
    matches=maximum_assignment([[x if x>=minimum_iou else 0 for x in r] for r in weights])
    matches=[(i,j) for i,j in matches if weights[i][j]>=minimum_iou]
    pairs=[{"strict_index":i,"fast_index":j,"iou":weights[i][j],
            "strict_text":strict[i]["text"],"fast_text":fast[j]["text"],
            "exact_text":strict[i]["text"]==fast[j]["text"],
            "character_distance":character_distance(strict[i]["text"],fast[j]["text"])}
           for i,j in matches]
    si,fj={i for i,j in matches},{j for i,j in matches}
    return {"strict_lines":len(strict),"fast_lines":len(fast),"matched":len(pairs),
            "missing_strict_indices":[i for i in range(len(strict)) if i not in si],
            "extra_fast_indices":[j for j in range(len(fast)) if j not in fj],
            "exact_text_matches":sum(p["exact_text"] for p in pairs),
            "character_distance":sum(p["character_distance"] for p in pairs),"pairs":pairs}
