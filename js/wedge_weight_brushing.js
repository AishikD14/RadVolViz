pp1 = [];
pp2 = [];
pp3 = [];
pp4 = [];
pp5 = [];
pp6 = [];

need_val = [];
need_keys = [];

// Clearing the brush on Parallel Coordinates
function clearBrush() {
  need_val = [];
  guiControls.minCe = 0.0;
  guiControls.minCo = 0.0;
  guiControls.minFe = 0.0;
  guiControls.minGd = 0.0;
  guiControls.maxCe = 1.0;
  guiControls.maxCo = 1.0;
  guiControls.maxFe = 1.0;
  guiControls.maxGd = 1.0;
}

// Being called on nearly every interaction with dashboard
function helloWorld() {
  console.log("Hello World");

  var seed = 1;
  function random() {
    var x = Math.sin(seed++) * 10000;
    return x - Math.floor(x);
  }

  // console.log(data);
  var rowName = rowHeader(data);
  //console.log(guiControls.defaultLens);
  rotateVar = guiControls.rotateVar3D / 57.32;
  binNum = guiControls.binValue;
  radialVal = guiControls.radialValue;
  // moveXCord = guiControls.xValue;
  // moveYCord = guiControls.yValue;
  modeARC = guiControls.modeARC;
  startAng = guiControls.startAng;
  arcWidth = guiControls.arcWidth;
  angleofLens = guiControls.lensAng;
  lensMovement = guiControls.lensMove;
  embedMode = guiControls.modeGBC;
  moveCradius = guiControls.radiusR;

  var ss = 0;
  var datum = ObjtoArr(data);

  if (embedMode == 1 || embedMode == 3) {
    ss = GBC(datum, rotateVar);
  }
  else if (embedMode == 2) {
    ss = DGBC(datum, rotateVar);
  }

  var x = d3.scale.linear().domain([-1, 1]);
  var y = d3.scale.linear().domain([-1, 1]);

  var row = ss.length;
  var col = ss[0].length;
  // console.log(col);
  var newarr = [];
  for (var i = 0; i < row - 4; i++) {
    newarr[i] = [];
    for (var j = 0; j < col; j++) {
      newarr[i][j] = ss[i][j];
      // newarr[i][j] = ss[i][j];
      // newarr[i][j] = ss[i][j];
      // newarr[i][j] = ss[i][j];
      // newarr[i][j] = ss[i][j];
    }
  }

  var vararr = [];
  for (var i = row - 4, j = 0; i < row, j < 4; i++, j++) {
    vararr[j] = [];
    vararr[j][0] = ss[i][0];
    vararr[j][1] = ss[i][1];
  }

  //var binNum = 25;

  var hist2d;
  hist2d = d3.hist2d()
    .bins(binNum)
    .indices([0, 1])
    .domain([x.domain(), y.domain()])
    (newarr, draw);

  var n = 0;
  var r = [];
  var filterdata = [];

  function draw(hist) {
    histN = hist;

    var P = [];
    var Q = [];
    var T = 0;

    for (var i = 0; i < hist.length; i++) {
      if (hist[i].length > 500) {
        var P = [];
        while (P.length < 5 * Math.log2(hist[i].length)) {
          var rd = Math.floor(random() * hist[i].length) + 1;
          if (P.indexOf(rd) > -1) continue;
          P[P.length] = rd;
          Q.push(hist[i][rd - 1]);
        }
      }
      else if (hist[i].length < 500 & hist[i].length > 50) {
        var P = [];
        while (P.length < Math.log2(hist[i].length)) {
          var rd = Math.floor(random() * hist[i].length) + 1;
          if (P.indexOf(rd) > -1) continue;
          P[P.length] = rd;

          Q.push(hist[i][rd - 1]);
        }
      }
      else {
        var P = [];
        while (P.length < hist[i].length / 2) {
          var rd = Math.floor(random() * hist[i].length) + 1;
          if (P.indexOf(rd) > -1) continue;
          P[P.length] = rd;
          Q.push(hist[i][rd - 1]);
        }
      }
    }

    for (ij = 0, T; ij < 4; ij++, T++) {
      Q[T] = vararr[ij];
    }

    var m = (ss).length;

    var n = Object.keys(datum[0]).length;

    var varPoints = new Array();
    for (var i = 0; i < n; i++) {
      varPoints.push(new Object());
    }

    for (var i = 0; i < n; i++) {
      varPoints[i].GBCX = ss[m - n + i][0];
      varPoints[i].GBCY = ss[m - n + i][1];
      varPoints[i].NAME = rowName[0][i];
    }

    let This = this;
    var colorSpaceWidth = 400;//document.getElementById(this.iconColorSpaceContainerId).clientWidth;
    var colorSpaceHeight = 400;//this.colorSpaceWidth;
    var diameter = Math.round(colorSpaceHeight * 2.4 / 3.1);
    var radiusC = diameter / 2;
    // console.log(radiusC);

    var xoffset = (colorSpaceWidth - diameter) / 2;
    var yoffset = (colorSpaceHeight - diameter) / 2;
    var centerX = xoffset + radiusC;
    var centerY = yoffset + radiusC;
    var scaleGBC2Canvas = d3.scale.linear().domain([-1, 1]).range([xoffset, xoffset + diameter]);
    var scaleGBC2Canvas = d3.scale.linear().domain([-1, 1]).range([yoffset, yoffset + diameter]);

    d3.select("#hello")
      .selectAll("svg").remove();

    // draw color space
    var canvas = document.createElement("canvas");
    d3.select(canvas)
      .attr("width", colorSpaceWidth)
      .attr("height", colorSpaceHeight);

    var context = canvas.getContext("2d");

    for (let i = xoffset; i < xoffset + diameter; i++) {
      for (let j = yoffset; j < yoffset + diameter; j++) {
        if (guiControls.brushMode == 1.0) {
          context.fillStyle = CoordToColor_ring(scaleGBC2Canvas.invert(j), scaleGBC2Canvas.invert(i), false);
        }
        else {
          context.fillStyle = CoordToColor(scaleGBC2Canvas.invert(j), scaleGBC2Canvas.invert(i), false);
        }
        context.fillRect(j, i, 1, 1);
        //  context.fillStyle = CoordToColor(scaleGBC2Canvas.invert(j), scaleGBC2Canvas.invert(i), false);
      }
    }

    // d3.select("#tipDiv")
    //   .selectAll("svg").remove();

    svgColorSpace = d3.select("#hello")
      .append("svg")
      .attr("width", colorSpaceWidth)
      .attr("height", colorSpaceHeight);
    svgColorSpace.append("image")
      .attr("xlink:href", canvas.toDataURL("image/png"))
      .attr("x", 0)
      .attr("y", 0)
      .attr("width", colorSpaceWidth)
      .attr("height", colorSpaceHeight);


    // var startAngle = startAng * (Math.PI/180.0);
    // var endAngle = arcWidth;
    // var s_x = Math.cos(startAngle);
    // var s_y = Math.sin(startAngle);
    // var e_x = Math.cos(arcWidth);
    // var e_y = Math.sin(arcWidth);
    //
    //   if (endAngle < startAng)
    //   {
    //     endAngle = endAngle + 2.0 * Math.PI;
    //   }
    //
    //   // document.getElementById('#tipDiv').innerHTML = "";
    //
    //   var half_angle = (endAngle - startAng) / 2.0;
    //   var mid_angle  = (endAngle + startAng) / 2.0;
    //   var cos_half_angle = Math.cos(half_angle);

    // var tool_tip = d3.tip()
    //  .attr("class", "d3-tip")
    //   .offset([20, 120])
    //   // .rootElement(document.getElementById('tools'))
    //   .html("<div id='tipDiv'></div>");
    // console.log("For Filtering Val", need_val);
    // console.log("For Filtering Key", need_keys);
    // console.log("All IDE points", Q);
    // var filtered = arr.filter(function (dataRow) {
    //   return dataRow[2] === 'Red';
    // });

    // Ce: x[2],
    // Co: x[3],
    // Fe: x[4],
    // Gd: x[5]

    for (var i = 0; i < need_keys.length; i++) {
      if (need_keys[i].key == "Ce") {
        Q = Q.filter(function (dataRow) {
          return dataRow[2] > need_val[i][0];
        });
        Q = Q.filter(function (dataRow) {
          return dataRow[2] <= need_val[i][1];
        });
      }
    }
    // console.log(Q);
    // svgColorSpace.call(tool_tip);
    var numCh = n;
    // console.log(varPoints[0].NAME);
    var main = svgColorSpace.append('g');
    var g = main.append("svg:g");

    g.selectAll("scatter-dots")
      .data(Q)
      .enter()
      .append("circle")
      .attr("cx", function (d, i) {
        if (embedMode != 3)
          return scaleGBC2Canvas(d[0]);
        else {
          return scaleGBC2Canvas(d[0]);
        }
      })
      .attr("cy", function (d) {
        if (embedMode != 3)
          return scaleGBC2Canvas(d[1]);
        else {

          return scaleGBC2Canvas(d[1]);
        }
      })
      .attr("r", function (d, i) {
        return 2.5;
      })

      .style("fill", function (d) {
        //  var angleArc = Math.atan2(scaleGBC2Canvas(d[1])-centerY,scaleGBC2Canvas(d[0])-centerX);//*180.0/Math.PI;
        //  console.log(mid_angle);
        //    var d_x = (scaleGBC2Canvas(d[0]) - centerX);
        //    var d_y = (scaleGBC2Canvas(d[1]) - centerY);
        //  if( ((s_x * d_y) - (s_y * d_x) >= 0.0)  && ((e_x * d_y) - (e_y * d_x) <= 0.0))
        //  if(Math.cos(angleArc - mid_angle) >= cos_half_angle)
        //  {
        return GBCtoHCL_ring(d[0], d[1]);
        //  }
        //  else {
        //    return "white";
        //  }

      })

      // .style("fill", function(d){
      //   if (embedMode != 3.0)
      //   {
      //     // console.log(d);
      //    return GBCtoHCL2(d[0],d[1])
      //    }
      //    else {
      //      return PC_Color(d);
      //    }
      //  })

      .style("stroke", "black")
      .style("stroke-opacity", 0.5)
      //   .style("opacity", function (d) {
      //
      //   dist = Math.sqrt((scaleGBC2Canvas(d[0]) - centerX)*(scaleGBC2Canvas(d[0])- centerX) + (scaleGBC2Canvas(d[1])-centerY)*(scaleGBC2Canvas(d[1])-centerY));
      //   if(dist < radialVal)
      //   return 0.1;
      //   else {
      //     return guiControls.alphaCorrection;
      //   }
      // })
      //ADDING TOOLTIP TO SHOW OTHER FOUR VALUES
      .on('mouseover', function (d) {
        // var ip = {};

        var ip = new Array(4);

        var vari = []
        var varNew = []

        var ip1 = [];
        var ip2 = [];
        var ip3 = [];
        var ip4 = [];
        var ip5 = [];
        std = []
        std1 = 0;
        std2 = 0;
        std3 = 0;
        std4 = 0;
        //document.getElementsByClassName('d3-tip').innerHTML = "";
        // svgColorSpace.call(tool_tip);
        // tool_tip.show();
        selectedX = d[0]
        selectedY = d[1]

        document.getElementById('tipDiv').innerHTML = "";

        // d3.select("#tipDiv")
        //   .selectAll("svg").remove();
        var tipSVG = d3.select("#tipDiv")
          .append("svg")
          .attr("width", 300)
          .attr("height", 70)
          .attr('x', 100)
          .attr('y', 800);

        tipSVG.selectAll('rect')
          .data(d)
          .enter()
          .append("rect")
          .attr("fill", function (d, i) {
            return 'steelblue';
          })
          .attr('x', 20)
          .attr("y", function (d, i) {
            if (i > 1) {
              return (i - 2) * (60 / numCh + 2) + 1
            }
          })
          // .attr("width", 0)
          .attr("height", 60 / numCh)
          .transition()
          .duration(10)
          .attr("width", function (d, i) {
            if (i > 1) {
              return 400 * d;
            }
          });

        for (var i = 0; i < varPoints.length; i++) {
          tipSVG.append('text')
            .attr('y', i * (60 / numCh + 2) - 2)
            .attr('x', 2)
            .attr('dy', '1.0em')
            .attr('text-anchor', 'left')
            // .text('Hello World How are you?')
            .text(varPoints[i].NAME)
            .style('fill', "#ffffff");
        }
        // tipSVG.

        if (guiControls.defaultLens == true) {

          tipSVG.selectAll("rect")
            .data(Q)
            .enter()

            // tipSVG
            .append('rect')
            // .attr("fill", "yellow")
            .attr('fill', function (d, i) {
              // console.log(d);
              dist = Math.sqrt((scaleGBC2Canvas(d[0]) - (moveXCord + 200)) * (scaleGBC2Canvas(selectedX) - (moveXCord + 200)) + (scaleGBC2Canvas(selectedY) - (moveYCord + 200)) * (scaleGBC2Canvas(selectedY) - (moveYCord + 200)));
              dd = moveCradius * moveCradius - dist * dist
              dist2 = Math.sqrt((scaleGBC2Canvas(d[0]) - (moveXCord + 200)) * (scaleGBC2Canvas(d[0]) - (moveXCord + 200)) + (scaleGBC2Canvas(d[1]) - (moveYCord + 200)) * (scaleGBC2Canvas(d[1]) - (moveYCord + 200)));

              dd2 = moveCradius * moveCradius - dist2 * dist2
              if (dd2 > 0) {
                // console.log("Inside");
                // for (var i = 2; i < n+2; i++) {
                // ip[0].push(d[2])

                //  for (ii=0;ii<n;ii++) {
                //   ip[ii]=new Array();
                //   for (j=2;j<n+2;j++) {
                //    ip[i].push(d[j]);
                //   }
                // }
                // console.log(ip[1].push(d[2]));
                // console.log(d[5]);
                ip1.push(d[2])
                ip2.push(d[3])
                ip3.push(d[4])
                if (d[5] != undefined) {
                  // console.log(ip4);
                  ip4.push(d[5])
                }
                if (d[6] != undefined) {
                  // console.log(ip5);
                  ip5.push(d[6])
                }

                // console.log(ip3);
                std12 = d3.variance(ip1)
                std22 = d3.variance(ip2)
                std32 = d3.variance(ip3)
                std42 = d3.variance(ip4)
                std52 = d3.variance(ip5)
                std = [std12, std22, std32, std42, std52]
                // }
                // for (var i = 2; i < n; i++) {
                //   array[i]
                // }
                // console.log(ip1);
                // console.log(std);
              }
              // else{
              //   // console.log("outside");
              // }
              return '#f4af1b'
              // console.log(scaleGBC2Canvas(selectedX), Math.floor(dist), moveXCord);
              //   if(dist < moveCradius){
              //     j = i
              //   // console.log(j);
              //   return 'yellow';
              // }
              //   else {
              //     // console.log("Coloring Section");
              //     // console.log(std);
              //     return 'blue';
              //   }
            })
            // .attr("y", function (d,i) {
            //   if (i >1) {
            //   return (i-4)*12+1;
            //   }
            // })
            .attr('x', 20)
            .attr('y', 4)
            .attr("width", 0)
            .attr("height", function (d, i) {
              // console.log(i);
              return 30 / numCh;
            })
            .transition()
            .duration(10)
            .attr('width', 2000 * std[0]);
          // .attr("width", function(d,i){
          //   if (i >1){
          //   return 500*d;
          // }
          // });
          for (var i = 1; i < n; i++) {
            tipSVG.append("rect")
              .attr("fill", "#f4af1b")
              .attr('x', 20)
              .attr("y", i * (60 / numCh + 2) + 5)
              // .attr("width", 0)
              .attr("height", 30 / numCh)
              .transition()
              .duration(10)
              .attr("width", 2000 * std[i]);
          }


          // tipSVG.append("rect")
          //   .attr("fill", "yellow")
          //   .attr("y", 38)
          //   // .attr("width", 0)
          //   .attr("height", 30/numCh)
          //   .transition()
          //   .duration(10)
          //   .attr("width", 5000*std[2]);

          // tipSVG.append("text")
          //   .text(d[0])
          //   .attr("x", 20)
          //   .attr("y", 45)
          //   .transition()
          //   .duration(10)
          //   .attr("x",  scaleGBC2Canvas(d[1])/3)
        }
        // tipSVG.append("text")
        //   .text(d[0])
        //   .attr("x", 10)
        //   .attr("y", 25)
        //   .transition()
        //   .duration(10)
        //   .attr("x",   function(d,i){
        //     return scaleGBC2Canvas(d[i])/3
        //   })

        // tipSVG.append("rect")
        //   .attr("fill", "red")
        //   .attr("y", 32)
        //   // .attr("width", 0)
        //   .attr("height", 20)
        //   .transition()
        //   .duration(10)
        //   .attr("width", scaleGBC2Canvas(d[1]));
        //
        // tipSVG.append("text")
        //   .text(d[0])
        //   .attr("x", 20)
        //   .attr("y", 45)
        //   .transition()
        //   .duration(10)
        //   .attr("x",  scaleGBC2Canvas(d[1])/3)

      });
    // .on('mouseout', tool_tip.hide);


    //lensAng = Math.atan(moveYCord/moveXCord);

    var variablePoints = svgColorSpace.append('g');
    var g = variablePoints.append("svg:g");

    g.selectAll("scatter-dots")
      .data(varPoints)
      .enter()
      .append("circle")
      .attr("cx", function (d, i) { return scaleGBC2Canvas(d.GBCX * 0.997); })
      .attr("cy", function (d) { return scaleGBC2Canvas(d.GBCY * 0.997); })
      .attr("r", function (d, i) { return 6; })
      //.style("fill","white")
      .style("fill", function (d) { return GBCtoHCL_ring(d.GBCX * 0.997, d.GBCY * 0.997) });
    // .style("stroke","red")
    // .style("stroke-opacity",1)
    // .style("opacity", 1);


    var variablePoints = svgColorSpace.append('g');
    var g = variablePoints.append("svg:g");

    g.selectAll("g")
      .data(varPoints)
      .enter()
      .append("text")
      .attr("x", function (d, i) {

        return scaleGBC2Canvas(d.GBCX * 0.997);
      })
      .attr("y", function (d) { return scaleGBC2Canvas(d.GBCY * 0.997); })
      .attr("dy", function (d, i) {

        // console.log(d);
        if (d.GBCY < 0) {
          return "-.230em";
        }
        else
          return ".531em";
      })

      .attr("dx", function (d, i) {
        if (d.GBCX < 0) {
          return "-1.40em";
        }
        else
          return ".35em";
      })
      .text(function (d, i) { return d.NAME; })
      .style('font-size', "30px")
      .style("fill", "black")
      .style("stroke", "white")
      .style("stroke-opacity", 1)
      .style("opacity", 1);


    //CIRCLE for using it as a Selection Parameters
    // lensMovement = 1 = TRANSLATIONAL
    if (modeARC == 1 && guiControls.defaultLens == true) {
      moveXCord = guiControls.xValue;
      moveYCord = guiControls.yValue;
      var g = svgColorSpace.append("svg:g");
      g.selectAll("g")
        .data([{ x: moveXCord, y: moveYCord }])
        .enter()
        .append("circle")
        .attr("cx", function (d) { return fromCartesianX(d.x, d.y, moveCradius); })
        .attr("cy", function (d) { return fromCartesianY(d.x, d.y, moveCradius); })
        .attr("r", moveCradius)
        .style("fill", function (d) {
          // dist = Math.sqrt((scaleGBC2Canvas(d[0]) - fromCartesianX(d.x,d.y,moveCradius))*(scaleGBC2Canvas(d[0])- fromCartesianX(d.x,d.y,moveCradius)) + (scaleGBC2Canvas(d[1])-fromCartesianY(d.x,d.y,moveCradius))*(scaleGBC2Canvas(d[1])-fromCartesianY(d.x,d.y,moveCradius)));
          // console.log(dist);
          return "none"
        })
        .style("opacity", 0.5)
        .style("stroke", "red")
        .style("stroke-width", 10)
        .style("stroke-opacity", 0.9)
        .call(d3.drag()
          .subject(function (d) { return { x: fromCartesianX(d.x, d.y, moveCradius), y: fromCartesianY(d.x, d.y, moveCradius) }; })
          .on("drag", dragged)
        );
      /*                           .call(d3.drag()
                                 .subject(function(d) { return {x: fromCartesianX(d.x), y: fromCartesianY(d.y)}; })
                                 .on("drag", dragged)
                               );*/

      function fromCartesianX(x, y, moveCradius) {
        //  console.log(x);
        return centerX + x;
      }

      function fromCartesianY(x, y, moveCradius) {
        return centerY + y;
      }

      function toCartesianX(x) {
        return x - centerX;
      }

      function toCartesianY(y) {

        return y - centerY - 230;
      }
      function dragged(d) {
        //console.log("hello");

        d.x = toCartesianX(d3.event.x);
        d.y = toCartesianY(d3.event.y);
        guiControls.xValue = d.x;//-2*centerX;
        guiControls.yValue = d.y;//-2*centerY;
        //  console.log(guiControls.xValue,guiControls.yValue);

        d3.select(this)
          .attr("cx", d3.event.x)
          .attr("cy", d3.event.y);
      }
    }

    if (guiControls.brushMode == 1.0) {
      brushingCode();
    }

    /// Parallel Coordinate

    var margin = { top: 18, right: 20, bottom: 0, left: 50 },
      width = 300,
      height = 135 - margin.top - margin.bottom,
      innerHeight = height - 2;

    var devicePixelRatio = window.devicePixelRatio || 1;
    // console.log(devicePixelRatio);
    var color = d3.scale.linear()
      // .range(['#1b9e77','#d95f02','#7570b3','#e7298a']);
      .range(['#e66101', '#2c7bb6']);

    var types = {
      "Number": {
        key: "Number",
        coerce: function (d) { return +d; },
        extent: d3.extent,
        within: function (d, extent) { return extent[0] <= d && d <= extent[1]; },
        defaultScale: d3.scale.linear().range([innerHeight, 0])
      },
      "String": {
        key: "String",
        coerce: String,
        extent: function (dataPC) { return dataPC.sort(); },
        within: function (d, extent, dim) { return extent[0] <= dim.scale(d) && dim.scale(d) <= extent[1]; },
        defaultScale: d3.scale.ordinal().rangePoints([0, innerHeight])
      }
    };

    var dimensions = [
      {
        key: "Ce",
        description: "Ce",
        type: types["Number"]
      },
      {
        key: "Co",
        description: "Co ",
        type: types["Number"]
      },
      {
        key: "Fe",
        type: types["Number"],
        description: "Fe"
      },
      {
        key: "Gd",
        type: types["Number"],
        description: "Gd"
      }
    ];

    var pc_data = Q.map(function (x) {
      return {
        gbxx: x[0],
        gbxy: x[1],
        Ce: x[2],
        Co: x[3],
        Fe: x[4],
        Gd: x[5]
      };
    });

    var xscalePC = d3.scale.ordinal()
      .domain(d3.range(dimensions.length))
      .rangePoints([0, width]);

    var yAxisPC = d3.svg.axis()
      .orient("left");

    document.getElementById('pcDiv').innerHTML = "";

    var containerPC = d3.select("#pcDiv").append("div")
      .attr("class", "parcoords")
      .style("width", width + margin.left + margin.right + "px")
      .style("height", height + margin.top + margin.bottom + "px");

    var svgPC = containerPC.append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var canvasPC = containerPC.append("canvas")
      .attr("width", width * devicePixelRatio)
      .attr("height", height * devicePixelRatio)
      .style("width", width + "px")
      .style("height", height + "px")
      .style("margin-top", margin.top + "px")
      .style("margin-left", margin.left + "px");

    var ctxPC = canvasPC.node().getContext("2d");
    ctxPC.globalCompositeOperation = 'darken';
    ctxPC.globalAlpha = 0.95;
    ctxPC.lineWidth = 1.5;
    ctxPC.scale(devicePixelRatio, devicePixelRatio);

    var axesPC = svgPC.selectAll(".axis")
      .data(dimensions)
      .enter().append("g")
      .attr("class", function (d) { return "axis " + d.key.replace(/ /g, "_"); })
      .attr("transform", function (d, i) { return "translate(" + xscalePC(i) + ")"; });

    dataPC = pc_data;

    dataPC.forEach(function (d) {
      dimensions.forEach(function (p) {
        d[p.key] = !d[p.key] ? null : p.type.coerce(d[p.key]);
      });

      // truncate long text strings to fit in data table
      for (var key in d) {
        if (d[key] && d[key].length > 35) d[key] = d[key].slice(0, 36);
      }
    });

    // type/dimension default setting happens here
    dimensions.forEach(function (dim) {
      if (!("domain" in dim)) {
        // detect domain using dimension type's extent function
        dim.domain = d3.functor(dim.type.extent)(dataPC.map(function (d) { return d[dim.key]; }));
      }
      if (!("scale" in dim)) {
        // use type's default scale for dimension
        dim.scale = dim.type.defaultScale.copy();
      }
      dim.scale.domain(dim.domain);
    });

    var renderPC = renderQueue(draw);

    ctxPC.clearRect(0, 0, width, height);
    ctxPC.globalAlpha = d3.min([0.85 / Math.pow(dataPC.length, 0.3), 1]);
    if (need_val.length == 0) {
      renderPC(dataPC);
    }
    else {
      renderPC(selected);
    }

    axesPC.append("g")
      .each(function (d) {
        var renderAxis = "axis" in d
          ? d.axis.scale(d.scale)  // custom axis
          : yAxisPC.scale(d.scale);  // default axis
        d3.select(this).call(renderAxis);
      })
      .append("text")
      .attr("class", "title")
      .attr("text-anchor", "start")
      .text(function (d) { return "description" in d ? d.description : d.key; });

    // Add and store a brush for each axis.
    axesPC.append("g")
      .attr("class", "brush")
      .each(function (d) {
        d3.select(this).call(d.brush = d3.svg.brush()
          .y(d.scale)
          .on("brushstart", brushstart)
          .on("brush", brush));
      })
      .selectAll("rect")
      .attr("x", -8)
      .attr("width", 16);

    d3.selectAll(".axis.Ce .tick text");

    function project(d) {
      return dimensions.map(function (p, i) {
        // check if data element has property and contains a value
        if (
          !(p.key in d) ||
          d[p.key] === null
        ) return null;

        return [xscalePC(i), p.scale(d[p.key])];
      });
    };

    function draw(d) {
      // console.log(d);
      if (d.Ce) {
        // console.log(PC_Color(ObjtoArrPC(d)));
        ctxPC.strokeStyle = PC_Color(ObjtoArrPC(d));
      }
      // ctxPC.strokeStyle = color(d.Ce);
      ctxPC.beginPath();
      var coords = project(d);
      coords.forEach(function (p, i) {
        // this tricky bit avoids rendering null values as 0
        if (p === null) {
          // this bit renders horizontal lines on the previous/next
          // dimensions, so that sandwiched null values are visible
          if (i > 0) {
            var prev = coords[i - 1];
            if (prev !== null) {
              ctxPC.moveTo(prev[0], prev[1]);
              ctxPC.lineTo(prev[0] + 6, prev[1]);
            }
          }
          if (i < coords.length - 1) {
            var next = coords[i + 1];
            if (next !== null) {
              ctxPC.moveTo(next[0] - 6, next[1]);
            }
          }
          return;
        }

        if (i == 0) {
          ctxPC.moveTo(p[0], p[1]);
          return;
        }

        ctxPC.lineTo(p[0], p[1]);
      });
      ctxPC.stroke();
    }

    function brushstart() {
      d3.event.sourceEvent.stopPropagation();
    }

    // Handles a brush event, toggling the display of foreground lines.
    function brush() {
      var actives = dimensions.filter(function (p) { return !p.brush.empty(); }),
        extents = actives.map(function (p) { return p.brush.extent(); });

      selected = dataPC.filter(function (d) {
        if (actives.every(function (dim, i) {
          // test if point is within extents for each active brush

          return dim.type.within(d[dim.key], extents[i], dim);
        })) {
          return true;
        }


        // console.log(extents);
      });

      ctxPC.clearRect(0, 0, width, height);
      ctxPC.globalAlpha = d3.min([0.85 / Math.pow(selected.length, 0.3), 1]);
      renderPC(selected);

      need_keys = actives;
      need_val = extents;
    }
  }
}

// Control Parallel Coordinate functions 
function brushedPC() {
  console.log(need_val);
  // console.log(selected);
  console.log(need_keys);
  guiControls.minCe = need_val[0];

  for (var i = 0; i < need_keys.length; i++) {
    // console.log(actives[i].key);
    if (need_keys[i].key == "Ce") {
      guiControls.minCe = need_val[i][0];
      guiControls.maxCe = need_val[i][1];
      // console.log("CE Brushing");
    }
    if (need_keys[i].key == "Co") {
      guiControls.minCo = need_val[i][0];
      guiControls.maxCo = need_val[i][1];
      // console.log("CO Brushing");
    }
    if (need_keys[i].key == "Fe") {
      guiControls.minFe = need_val[i][0];
      guiControls.maxFe = need_val[i][1];
      // console.log("FE Brushing");
    }
    if (need_keys[i].key == "Gd") {
      guiControls.minGd = need_val[i][0];
      guiControls.maxGd = need_val[i][1];
      // console.log("GD Brushing");
    }
  }
  // console.log(extents[0]);
  // console.log(extents[i][1]);
  // }


}
