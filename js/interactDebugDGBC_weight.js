function Vcorrelation(X, Y) {

    var n = X.length;

    var sumXY = 0.0;
    var sumX = 0.0;
    var sumY = 0.0;
    var sumX2 = 0.0;
    var sumY2 = 0.0;
    for (var i = 0; i < n; i++) {
        sumXY = sumXY + X[i] * Y[i];
        sumX = sumX + parseFloat(X[i]);
        sumY = sumY + parseFloat(Y[i]);
        sumX2 = sumX2 + X[i] * X[i];
        sumY2 = sumY2 + Y[i] * Y[i];
    }

    var r;
    if (((sumX2 - sumX * sumX / n) * (sumY2 - sumY * sumY / n)) == 0) {
        r = 1.0;
    }
    else {
        r = (sumXY - sumX * sumY / n) / Math.sqrt((sumX2 - sumX * sumX / n) * (sumY2 - sumY * sumY / n));
    }
    return r;

};



function getShortestHamiltonianCycle(dist) {

    var n = dist.length;
    var nn = Math.pow(2, n);
    var dp = new Array(1 << n);

    for (var i = 0; i < dp.length; i++) {
        dp[i] = new Array(n);
        for (var j = 0; j < n; j++) {
            dp[i][j] = 1000000;//1000000f;
        }
    }
    //console.log(dp)
    dp[1][0] = 0;
    for (var mask = 1; mask < 1 << n; mask += 2) {
        for (var i = 1; i < n; i++) {
            if ((mask & 1 << i) != 0) {
                for (var j = 0; j < n; j++) {
                    if ((mask & 1 << j) != 0) {
                        dp[mask][i] = Math.min(dp[mask][i], dp[mask ^ (1 << i)][j] + dist[j][i]);
                        //                          console.log(mask);
                    }
                }
            }
        }
    }


    var res = 2000000;//2000000f;
    for (var i = 1; i < n; i++) {
        res = Math.min(res, dp[(1 << n) - 1][i] + dist[i][0]);
    }

    // reconstruct path
    var cur = (1 << n) - 1;
    var order = new Array(n);//new int[n];
    order[0] = 0;
    //  console.log(cur);
    var last = 0;
    for (var i = n - 1; i >= 1; i--) {
        var bj = -1;
        for (var j = 1; j < n; j++) {
            if ((cur & 1 << j) != 0 && (bj == -1 || dp[cur][bj] + dist[bj][last] > dp[cur][j] + dist[j][last])) {
                bj = j;
            }
        }
        order[i] = bj;
        //            console.log(order);
        cur ^= 1 << bj;
        last = bj;
    }
    //      console.log(order);
    return order;

};


function DGBC(datam, rotateVar) {

    var m = datam.length;
    var n = (datam[0]).length;


    //console.log(datam)
    /*float[] tempx = new float[m];
    float[] tempy = new float[m];
    float[,] vertex = new float[n, n];*/
    var tempx = [];
    var tempy = [];

    var vert = new Array();
    //console.log(GBCLocation)
    for (i = 0; i < n; i++) {
        vert[i] = new Array();
        for (j = 0; j < n; j++) {
            vert[i][j] = 0;
        }
    }

    for (var i = 0; i < n; i++) {
        for (var j = 0; j < n; j++) {
            for (var k = 0; k < m; k++) {
                tempx[k] = datam[k][i];
                tempy[k] = datam[k][j];
            }
            vert[i][j] = (1 - Vcorrelation(tempx, tempy)) / 2;
        }
    }

    dimorder = getShortestHamiltonianCycle(vert);
    //console.log(dimorder);

    var sumcorr = 0.0;
    var corr = new Array(n);
    for (var i = 0; i < n; i++) {
        corr[i] = 1;
    }
    sumcorr = n;

    sumcorr = 0.0;
    corr = new Array(n);
    for (var i = 0; i < n - 1; i++) {
        corr[i] = vert[dimorder[i]][dimorder[i + 1]];
    }
    corr[n - 1] = vert[dimorder[n - 1]][dimorder[0]];

    sumcorr = n - 3;

    var angle = new Array(n);
    angle[0] = 0 + rotateVar;
    var GBCLocation = new Array(); // m+n,2 size array for Location

    for (i = 0; i < m + n; i++) {
        GBCLocation[i] = new Array();
        for (j = 0; j < 2; j++) {
            GBCLocation[i][j] = 0;
        }
    }

    GBCLocation[m][0] = Math.cos(angle[0]) * 0.997;
    GBCLocation[m][1] = Math.sin(angle[0]) * 0.997;


    for (var i = 1; i < n; i++) {
        angle[i] = angle[i - 1] + 2 * Math.PI * (corr[i - 1] / sumcorr);//+rotateVar;
        //console.log(angle[i]);
        //  console.log(corr[i-1]);
        GBCLocation[i + m][0] = Math.cos(angle[i]) * 0.997;
        //  console.log(GBCLocation[i + m][0]);
        GBCLocation[i + m][1] = Math.sin(angle[i]) * 0.997;
        //  console.log(GBCLocation[i + m][1]);
    }



    for (var i = 0; i < m; i++) {
        var tempsum = 0;
        for (var j = 0; j < n; j++) {
            tempsum = tempsum + parseFloat(datam[i][dimorder[j]]);
        }
        //    console.log(tempsum);
        GBCLocation[i][0] = 0;
        GBCLocation[i][1] = 0;
        if (tempsum == 0) {
            GBCLocation[i][0] = 0;
            GBCLocation[i][1] = 0;
        }
        else {
            for (var j = 0; j < n; j++) {
                GBCLocation[i][0] = GBCLocation[i][0] + (datam[i][dimorder[j]] / tempsum) * GBCLocation[m + j][0];
                GBCLocation[i][1] = GBCLocation[i][1] + (datam[i][dimorder[j]] / tempsum) * GBCLocation[m + j][1];
            }
        }
    }


    for (var i = 0; i < n; i++) {
        if (angle[i] < 0) {
            angle[i] = angle[i] + Math.PI * 2;
        }
        if (angle[i] > Math.PI * 2) {
            angle[i] = angle[i] - Math.PI * 2;
        }
    }
    //console.log(angle);
    angle.sort();

    for (var i = 0; i < m; i++) {
        var tempangle = Math.atan2(GBCLocation[i][1], GBCLocation[i][0]);
        if (tempangle < 0) { tempangle = tempangle + Math.PI * 2; }
        var flag = false;
        var tempA = 0.0;
        var tempB = 0.0;
        for (var j = 0; j < n - 1; j++) {
            if ((tempangle > angle[j] || tempangle == angle[j]) && (tempangle < angle[j + 1])) {
                tempA = angle[j + 1];
                tempB = angle[j];
                flag = true;
            }
            if (flag == true)
                break;
        }
        if (flag == false) {
            tempA = angle[0] + Math.PI * 2;
            tempB = angle[n - 1];
        }
        var lth = (Math.sqrt(GBCLocation[i][0] * GBCLocation[i][0] + GBCLocation[i][1] * GBCLocation[i][1]) / Math.cos((tempA - tempB) / 2) * Math.cos(-(tempA + tempB) / 2 + tempangle));
        GBCLocation[i][0] = (lth * Math.cos(tempangle));
        GBCLocation[i][1] = (lth * Math.sin(tempangle));
    }

    sumcorr = 0.0;
    corr = new Array(n);
    for (var i = 0; i < n - 1; i++) {
        corr[i] = vert[dimorder[i]][dimorder[i + 1]];
    }
    corr[n - 1] = vert[dimorder[n - 1]][dimorder[0]];

    return GBCLocation;

};
