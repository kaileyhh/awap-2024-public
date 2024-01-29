def print2DArr (bools):
    for i in range(len(bools)):
        for j in range(len(bools[0])):
            print(bools[i][j], ' ')
        print('\n')

# true if x, y is a valid start / end point (e.g. only has one path block touching it)
def isPoint (arr, x, y, n, m):
    numSurrounding = 0
    if (x-1 > 0 and arr[x-1][y][0] == 'P'):
        numSurrounding+=1
    if (y-1 > 0 and arr[x][y-1][0] == 'P'):
        numSurrounding+=1
    if (x+1 < n and arr[x+1][y][0] == 'P'):
        numSurrounding+=1
    if (y+1 < m and arr[x][y+1][0] == 'P'):
        numSurrounding+=1

    return (arr[x][y][0] == 'P' and numSurrounding == 1)

# checks the top, bottom, left, and right edge of the map for a "point" piece
def findStart (arr, n, m):
    for i in range(n):
        if isPoint(arr, i, 0, n, m):
            return [i, 0]
        elif isPoint(arr, i, m-1, n, m):
            return [i, m-1]
    for j in range(m):
        if isPoint(arr, 0, j, n, m):
            return [0, j]
        if isPoint(arr, n-1, j, n, m):
            return [n-1, j]
    return [-1, -1]

# generates a list of all "point" pieces as defined above
def getPoints (arr, n, m):
    points = []
    for i in range(n):
        if isPoint(arr, i, 0, n, m):
            points.append([i, 0])
        elif isPoint(arr, i, m-1, n, m):
            points.append([i, m-1])
    for j in range(m):
        if isPoint(arr, 0, j, n, m):
            points.append([0, j])
        if isPoint(arr, n-1, j, n, m):
            points.append([n-1, j])
    return points

# modifies path list to contain in-order coordinates of balloon path location, starting from r, c
def floodFill (arr, bools, r, c, n, m, path): 
    # out of bounds
    if r < 0 or r >= n or c < 0 or c >= m:
        return False
    # already seen
    if bools[r][c]:
        return False
    # valid path
    if arr[r][c][0] == 'P':
        path.append([r, c])
        bools[r][c] = True
    # not a path
    else:
        return False
    
    floodFill(arr, bools, r+1, c, n, m, path)
    floodFill(arr, bools, r, c-1, n, m, path)
    floodFill(arr, bools, r-1, c, n, m, path)
    floodFill(arr, bools, r, c+1, n, m, path)

def get_path(fname):
    import ast
    file = open(fname, 'r')
    arrAsStr = file.readline()
    file.close()

    arr = ast.literal_eval(arrAsStr)
    n = len(arr)
    m = len(arr[0])
    bools = [[False for i in range(m)] for j in range(n)]

    points = getPoints(arr, n, m)

    path = []
    for corr in points :
        if(corr not in path):
            currPath = []
            floodFill(arr, bools, corr[0], corr[1], n, m, currPath)
            path.extend(currPath)
    return path
