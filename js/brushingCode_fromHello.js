// Called from wedge_weight_brushing.js when manual data coloring is selected
function brushingCode() {

  pointLineonCir();

  var dragging = false, drawing = false, startPoint;
  var polyG = svgColorSpace.append('g');

  var points = []
  svgColorSpace.on('mouseup', function () {
    console.log("Mouse Up Entering");

    if (dragging) return;

    drawing = true;
    startPoint = [d3.mouse(this)[0], d3.mouse(this)[1]];

    guiControls.startX = startPoint[0];
    guiControls.startY = startPoint[1];

    if (polyG.select('g.drawPoly').empty()) {
      // console.log("drawpoly")
      g4 = polyG.append('g').attr('class', 'drawPoly');
    }

    // Not getting used as of now
    if (d3.event.target.hasAttribute('is-handle')) {
      console.log("Call polygon close");
      closePolygon();
      return;
    };

    points.push(d3.mouse(this));

    g4.select('polyline').remove();

    // Code after this seems to be not getting accessed as of now
    var polyline = svgColorSpace.append('polyline')
      .attr('points', points)
      .style('fill', 'none')
      .attr('stroke', '#000');

    for (var i = 0; i < points.length; i++) {
      polyline.append('circle')
        .attr('cx', points[i][0])
        .attr('cy', points[i][1])
        .attr('r', 6)
        .attr('fill', 'red')
        .attr('stroke', '#000')
        .style({ cursor: 'pointer' });
    }
  });

  // Not getting accessed as of now
  function closePolygon() {
    console.log("Enter PolygonClose");
    polyG.select('g.drawPoly').remove();
    var g = polyG.append('g');
    g.append('polygon')
      .attr('points', points)
      .style('fill', getRandomColor());
    for (var i = 0; i < points.length; i++) {
      var circle = g.selectAll('circles')
        .data([points[i]])
        .enter()
        .append('circle')
        .attr('cx', points[i][0])
        .attr('cy', points[i][1])
        .attr('r', 4)
        .attr('fill', '#FDBC07')
        .attr('stroke', '#000')
        .attr('is-handle', 'true')
        .style({ cursor: 'move' });
      // .call(dragger);
    }
    points.splice(0);
    drawing = false;
  }

  svgColorSpace.on('mousemove', function () {
    // console.log("Enter Mouse Move");

    if (!drawing) return;
    var g = d3.select('g.drawPoly');
    g.select('line').remove();

    var line = g.append('line')
      .attr('x1', startPoint[0])
      .attr('y1', startPoint[1])
      .attr('x2', d3.mouse(this)[0] + 2)
      .attr('y2', d3.mouse(this)[1])
      .attr('stroke', 'red')
      .attr('stroke-width', 1);
  })

  if (guiControls.polySide == 5.0) {
    if (pp1.length > 0) {
      guiControls.x1 = pp1[0][0];
      guiControls.y1 = pp1[0][1];

      guiControls.x2 = pp1[1][0];
      guiControls.y2 = pp1[1][1];

      guiControls.x3 = pp1[2][0];
      guiControls.y3 = pp1[2][1];

      guiControls.x4 = pp1[3][0];
      guiControls.y4 = pp1[3][1];

      // guiControls.x5 = pp1[4][0];
      // guiControls.y5 = pp1[4][1];

    }

    if (pp2.length > 0) {
      guiControls.x11 = pp2[0][0];
      guiControls.y11 = pp2[0][1];

      guiControls.x12 = pp2[1][0];
      guiControls.y12 = pp2[1][1];

      guiControls.x13 = pp2[2][0];
      guiControls.y13 = pp2[2][1];

      guiControls.x14 = pp2[3][0];
      guiControls.y14 = pp2[3][1];

      // guiControls.x15 = pp2[4][0];
      // guiControls.y15 = pp2[4][1];
    }

    if (pp3.length > 0) {
      guiControls.x31 = pp3[0][0];
      guiControls.y31 = pp3[0][1];

      guiControls.x32 = pp3[1][0];
      guiControls.y32 = pp3[1][1];

      guiControls.x33 = pp3[2][0];
      guiControls.y33 = pp3[2][1];

      guiControls.x34 = pp3[3][0];
      guiControls.y34 = pp3[3][1];

      // guiControls.x35 = pp3[4][0];
      // guiControls.y35 = pp3[4][1];
    }

    if (pp4.length > 0) {
      guiControls.x41 = pp4[0][0];
      guiControls.y41 = pp4[0][1];

      guiControls.x42 = pp4[1][0];
      guiControls.y42 = pp4[1][1];

      guiControls.x43 = pp4[2][0];
      guiControls.y43 = pp4[2][1];

      guiControls.x44 = pp4[3][0];
      guiControls.y44 = pp4[3][1];

      // guiControls.x45 = pp4[4][0];
      // guiControls.y45 = pp4[4][1];
    }

    if (pp5.length > 0) {
      guiControls.x51 = pp5[0][0];
      guiControls.y51 = pp5[0][1];

      guiControls.x52 = pp5[1][0];
      guiControls.y52 = pp5[1][1];

      guiControls.x53 = pp5[2][0];
      guiControls.y53 = pp5[2][1];

      guiControls.x54 = pp5[3][0];
      guiControls.y54 = pp5[3][1];

      // guiControls.x55 = pp5[4][0];
      // guiControls.y55 = pp5[4][1];
    }

  }

  if (guiControls.polySide == 6.0) {

    if (pp1.length > 0) {
      guiControls.x1 = pp1[0][0];
      guiControls.y1 = pp1[0][1];

      guiControls.x2 = pp1[1][0];
      guiControls.y2 = pp1[1][1];

      guiControls.x3 = pp1[2][0];
      guiControls.y3 = pp1[2][1];

      guiControls.x4 = pp1[3][0];
      guiControls.y4 = pp1[3][1];

      guiControls.x5 = pp1[4][0];
      guiControls.y5 = pp1[4][1];

      // guiControls.x6 = pp1[5][0];
      // guiControls.y6 = pp1[5][1];
    }

    if (pp2.length > 0) {
      guiControls.x11 = pp2[0][0];
      guiControls.y11 = pp2[0][1];

      guiControls.x12 = pp2[1][0];
      guiControls.y12 = pp2[1][1];

      guiControls.x13 = pp2[2][0];
      guiControls.y13 = pp2[2][1];

      guiControls.x14 = pp2[3][0];
      guiControls.y14 = pp2[3][1];

      guiControls.x15 = pp2[4][0];
      guiControls.y15 = pp2[4][1];

      // guiControls.x16 = pp2[5][0];
      // guiControls.y16 = pp2[5][1];

    }

    if (pp3.length > 0) {
      guiControls.x31 = pp3[0][0];
      guiControls.y31 = pp3[0][1];

      guiControls.x32 = pp3[1][0];
      guiControls.y32 = pp3[1][1];

      guiControls.x33 = pp3[2][0];
      guiControls.y33 = pp3[2][1];

      guiControls.x34 = pp3[3][0];
      guiControls.y34 = pp3[3][1];

      guiControls.x35 = pp3[4][0];
      guiControls.y35 = pp3[4][1];

      // guiControls.x36 = pp3[5][0];
      // guiControls.y36 = pp3[5][1];

    }

    if (pp4.length > 0) {
      guiControls.x41 = pp4[0][0];
      guiControls.y41 = pp4[0][1];

      guiControls.x42 = pp4[1][0];
      guiControls.y42 = pp4[1][1];

      guiControls.x43 = pp4[2][0];
      guiControls.y43 = pp4[2][1];

      guiControls.x44 = pp4[3][0];
      guiControls.y44 = pp4[3][1];

      guiControls.x45 = pp4[4][0];
      guiControls.y45 = pp4[4][1];

      // guiControls.x46 = pp4[5][0];
      // guiControls.y46 = pp4[5][1];

    }

    if (pp5.length > 0) {
      guiControls.x51 = pp5[0][0];
      guiControls.y51 = pp5[0][1];

      guiControls.x52 = pp5[1][0];
      guiControls.y52 = pp5[1][1];

      guiControls.x53 = pp5[2][0];
      guiControls.y53 = pp5[2][1];

      guiControls.x54 = pp5[3][0];
      guiControls.y54 = pp5[3][1];

      guiControls.x55 = pp5[4][0];
      guiControls.y55 = pp5[4][1];

      // guiControls.x56 = pp5[5][0];
      // guiControls.y56 = pp5[5][1];

    }
  }

  if (guiControls.polySide == 7.0) {
    if (pp1.length > 0) {
      guiControls.x1 = pp1[0][0];
      guiControls.y1 = pp1[0][1];

      guiControls.x2 = pp1[1][0];
      guiControls.y2 = pp1[1][1];

      guiControls.x3 = pp1[2][0];
      guiControls.y3 = pp1[2][1];

      guiControls.x4 = pp1[3][0];
      guiControls.y4 = pp1[3][1];

      guiControls.x5 = pp1[4][0];
      guiControls.y5 = pp1[4][1];

      guiControls.x6 = pp1[5][0];
      guiControls.y6 = pp1[5][1];

      // guiControls.x7 = pp1[6][0];
      // guiControls.y7 = pp1[6][1];
    }

    if (pp2.length > 0) {
      guiControls.x11 = pp2[0][0];
      guiControls.y11 = pp2[0][1];

      guiControls.x12 = pp2[1][0];
      guiControls.y12 = pp2[1][1];

      guiControls.x13 = pp2[2][0];
      guiControls.y13 = pp2[2][1];

      guiControls.x14 = pp2[3][0];
      guiControls.y14 = pp2[3][1];

      guiControls.x15 = pp2[4][0];
      guiControls.y15 = pp2[4][1];

      guiControls.x16 = pp2[5][0];
      guiControls.y16 = pp2[5][1];

      // guiControls.x17 = pp2[6][0];
      // guiControls.y17 = pp2[6][1];

    }

    if (pp3.length > 0) {
      guiControls.x31 = pp3[0][0];
      guiControls.y31 = pp3[0][1];

      guiControls.x32 = pp3[1][0];
      guiControls.y32 = pp3[1][1];

      guiControls.x33 = pp3[2][0];
      guiControls.y33 = pp3[2][1];

      guiControls.x34 = pp3[3][0];
      guiControls.y34 = pp3[3][1];

      guiControls.x35 = pp3[4][0];
      guiControls.y35 = pp3[4][1];

      guiControls.x36 = pp3[5][0];
      guiControls.y36 = pp3[5][1];

      // guiControls.x37 = pp3[6][0];
      // guiControls.y37 = pp3[6][1];
    }

    if (pp4.length > 0) {
      guiControls.x41 = pp4[0][0];
      guiControls.y41 = pp4[0][1];

      guiControls.x42 = pp4[1][0];
      guiControls.y42 = pp4[1][1];

      guiControls.x43 = pp4[2][0];
      guiControls.y43 = pp4[2][1];

      guiControls.x44 = pp4[3][0];
      guiControls.y44 = pp4[3][1];

      guiControls.x45 = pp4[4][0];
      guiControls.y45 = pp4[4][1];

      guiControls.x46 = pp4[5][0];
      guiControls.y46 = pp4[5][1];

      // guiControls.x47 = pp4[6][0];
      // guiControls.y47 = pp4[6][1];

    }

    if (pp5.length > 0) {
      guiControls.x51 = pp5[0][0];
      guiControls.y51 = pp5[0][1];

      guiControls.x52 = pp5[1][0];
      guiControls.y52 = pp5[1][1];

      guiControls.x53 = pp5[2][0];
      guiControls.y53 = pp5[2][1];

      guiControls.x54 = pp5[3][0];
      guiControls.y54 = pp5[3][1];

      guiControls.x55 = pp5[4][0];
      guiControls.y55 = pp5[4][1];

      guiControls.x56 = pp5[5][0];
      guiControls.y56 = pp5[5][1];

      // guiControls.x57 = pp5[6][0];
      // guiControls.y57 = pp5[6][1];

    }
  }

  if (guiControls.polySide == 8.0) {
    if (pp1.length > 0) {
      guiControls.x1 = pp1[0][0];
      guiControls.y1 = pp1[0][1];

      guiControls.x2 = pp1[1][0];
      guiControls.y2 = pp1[1][1];

      guiControls.x3 = pp1[2][0];
      guiControls.y3 = pp1[2][1];

      guiControls.x4 = pp1[3][0];
      guiControls.y4 = pp1[3][1];

      guiControls.x5 = pp1[4][0];
      guiControls.y5 = pp1[4][1];

      guiControls.x6 = pp1[5][0];
      guiControls.y6 = pp1[5][1];

      guiControls.x7 = pp1[6][0];
      guiControls.y7 = pp1[6][1];

      // guiControls.x8 = pp1[7][0];
      // guiControls.x8 = pp1[7][0];
    }

    if (pp2.length > 0) {
      guiControls.x11 = pp2[0][0];
      guiControls.y11 = pp2[0][1];

      guiControls.x12 = pp2[1][0];
      guiControls.y12 = pp2[1][1];

      guiControls.x13 = pp2[2][0];
      guiControls.y13 = pp2[2][1];

      guiControls.x14 = pp2[3][0];
      guiControls.y14 = pp2[3][1];

      guiControls.x15 = pp2[4][0];
      guiControls.y15 = pp2[4][1];

      guiControls.x16 = pp2[5][0];
      guiControls.y16 = pp2[5][1];

      guiControls.x17 = pp2[6][0];
      guiControls.y17 = pp2[6][1];

      // guiControls.x18 = pp2[7][0];
      // guiControls.y18 = pp2[7][1];
    }

    if (pp3.length > 0) {
      guiControls.x31 = pp3[0][0];
      guiControls.y31 = pp3[0][1];

      guiControls.x32 = pp3[1][0];
      guiControls.y32 = pp3[1][1];

      guiControls.x33 = pp3[2][0];
      guiControls.y33 = pp3[2][1];

      guiControls.x34 = pp3[3][0];
      guiControls.y34 = pp3[3][1];

      guiControls.x35 = pp3[4][0];
      guiControls.y35 = pp3[4][1];

      guiControls.x36 = pp3[5][0];
      guiControls.y36 = pp3[5][1];

      guiControls.x37 = pp3[6][0];
      guiControls.y37 = pp3[6][1];

      // guiControls.x38 = pp3[7][0];
      // guiControls.y38 = pp3[7][1];

    }

    if (pp4.length > 0) {
      guiControls.x41 = pp4[0][0];
      guiControls.y41 = pp4[0][1];

      guiControls.x42 = pp4[1][0];
      guiControls.y42 = pp4[1][1];

      guiControls.x43 = pp4[2][0];
      guiControls.y43 = pp4[2][1];

      guiControls.x44 = pp4[3][0];
      guiControls.y44 = pp4[3][1];

      guiControls.x45 = pp4[4][0];
      guiControls.y45 = pp4[4][1];

      guiControls.x46 = pp4[5][0];
      guiControls.y46 = pp4[5][1];

      guiControls.x47 = pp4[6][0];
      guiControls.y47 = pp4[6][1];

      // guiControls.x48 = pp4[7][0];
      // guiControls.y48 = pp4[7][1];

    }

    if (pp5.length > 0) {
      guiControls.x51 = pp5[0][0];
      guiControls.y51 = pp5[0][1];

      guiControls.x52 = pp5[1][0];
      guiControls.y52 = pp5[1][1];

      guiControls.x53 = pp5[2][0];
      guiControls.y53 = pp5[2][1];

      guiControls.x54 = pp5[3][0];
      guiControls.y54 = pp5[3][1];

      guiControls.x55 = pp5[4][0];
      guiControls.y55 = pp5[4][1];

      guiControls.x56 = pp5[5][0];
      guiControls.y56 = pp5[5][1];

      guiControls.x57 = pp5[6][0];
      guiControls.y57 = pp5[6][1];

      // guiControls.x58 = pp5[7][0];
      // guiControls.y58 = pp5[7][1];
    }
  }
}

// Clear marked cluster regions
function ClearSVGPoints() {
  console.log("ClearSVGPoints");

  guiControls.startX = 0.0;
  guiControls.startY = 0.0;

  for (i = 0; i < guiControls.polySide + 2; i++) {
    pp1.pop();
  }

  for (i = 0; i < guiControls.polySide + 2; i++) {
    pp2.pop();
  }

  for (i = 0; i < guiControls.polySide + 1; i++) {
    pp3.pop();
  }

  for (i = 0; i < guiControls.polySide + 1; i++) {
    pp4.pop();
  }

  for (i = 0; i < guiControls.polySide + 1; i++) {
    pp5.pop();
  }

  // for (i=0;i<guiControls.polySide+1;i++){
  //   pp6.pop();
  // }

  guiControls.x1 = 0.0;
  guiControls.x2 = 0.0;
  guiControls.x3 = 0.0;
  guiControls.x4 = 0.0;
  guiControls.x5 = 0.0;
  guiControls.x6 = 0.0;
  guiControls.x7 = 0.0;


  guiControls.y1 = 0.0;
  guiControls.y2 = 0.0;
  guiControls.y3 = 0.0;
  guiControls.y4 = 0.0;
  guiControls.y5 = 0.0;
  guiControls.y6 = 0.0;
  guiControls.y7 = 0.0;


  guiControls.x11 = 0.0;
  guiControls.x12 = 0.0;
  guiControls.x13 = 0.0;
  guiControls.x14 = 0.0;
  guiControls.x15 = 0.0;
  guiControls.x16 = 0.0;
  guiControls.x17 = 0.0;

  guiControls.y11 = 0.0;
  guiControls.y12 = 0.0;
  guiControls.y13 = 0.0;
  guiControls.x14 = 0.0;
  guiControls.x15 = 0.0;
  guiControls.x16 = 0.0;
  guiControls.x17 = 0.0;


  guiControls.x31 = 0.0;
  guiControls.x32 = 0.0;
  guiControls.x33 = 0.0;
  guiControls.x34 = 0.0;
  guiControls.x35 = 0.0;
  guiControls.x36 = 0.0;
  guiControls.x37 = 0.0;

  guiControls.y31 = 0.0;
  guiControls.y32 = 0.0;
  guiControls.y33 = 0.0;
  guiControls.y34 = 0.0;
  guiControls.y35 = 0.0;
  guiControls.y36 = 0.0;
  guiControls.y37 = 0.0;

  guiControls.x41 = 0.0;
  guiControls.x42 = 0.0;
  guiControls.x43 = 0.0;
  guiControls.x44 = 0.0;
  guiControls.x45 = 0.0;
  guiControls.x46 = 0.0;
  guiControls.x47 = 0.0;

  guiControls.y41 = 0.0;
  guiControls.y42 = 0.0;
  guiControls.y43 = 0.0;
  guiControls.y44 = 0.0;
  guiControls.y45 = 0.0;
  guiControls.y46 = 0.0;
  guiControls.y47 = 0.0;

  guiControls.x51 = 0.0;
  guiControls.x52 = 0.0;
  guiControls.x53 = 0.0;
  guiControls.x54 = 0.0;
  guiControls.x55 = 0.0;
  guiControls.x56 = 0.0;
  guiControls.x57 = 0.0;

  guiControls.y51 = 0.0;
  guiControls.y52 = 0.0;
  guiControls.y53 = 0.0;
  guiControls.y54 = 0.0;
  guiControls.y55 = 0.0;
  guiControls.y56 = 0.0;
  guiControls.y57 = 0.0;

  // guiControls.x61 = 0.0;
  // guiControls.x62 = 0.0;
  // guiControls.x63 = 0.0;
  // guiControls.x64 = 0.0;
  // guiControls.x65 = 0.0;
  //
  // guiControls.y61 = 0.0;
  // guiControls.y62 = 0.0;
  // guiControls.y63 = 0.0;
  // guiControls.y64 = 0.0;
  // guiControls.y65 = 0.0;
}

// Called on radio button change between data driven and manual coloring
function radioOnChange(value) {
  if (value == 'brush') {
    guiControls.brushMode = 1.0
  }
  else if (value == 'segment') {
    guiControls.brushMode = 2.0
  }
  else {
    guiControls.brushMode = 0.0
    ClearSVGPoints();
  }
}

// Example function to access a specific element in a 4D array
function getElement(data, shape, indices) {
  const [d1, d2, d3, d4] = shape;
  const [i1, i2, i3, i4] = indices;

  if (i1 >= d1 || i2 >= d2 || i3 >= d3 || i4 >= d4) {
      throw new Error('Indices out of bounds');
  }

  const index = (i1 * d2 * d3 * d4) + (i2 * d3 * d4) + (i3 * d4) + i4;
  return data[index];
}

// Check if cluster marking is completed
function checkClusterCompletion() {
  if (guiControls.clusters == 1.0){
    // console.log("Do check");
    console.log(pp1.length);
    if (guiControls.polySide == 5.0 && pp1.length == 5) {
      console.log("Cluster marking completed");
      segmentRegions(1,5);
    }
    else if (guiControls.polySide == 6.0 && pp1.length == 6) {
      console.log("Cluster marking completed");
      segmentRegions(1,6);
    }
    else if (guiControls.polySide == 7.0 && pp1.length == 7) {
      console.log("Cluster marking completed");
      segmentRegions(1,7);
    }
    else if (guiControls.polySide == 8.0 && pp1.length == 8) {
      console.log("Cluster marking completed");
      segmentRegions(1,8);
    }
    else{
      guiControls.clusterMarkingComplete = 0.0;
    }
  }
  else if (guiControls.clusters == 2.0){
    // console.log("Do check");
    console.log(pp1.length, pp2.length);
    if (guiControls.polySide == 5.0 && pp1.length == 5 && pp2.length == 5) {
      console.log("Cluster marking completed");
      segmentRegions(2,5);
    }
    else if (guiControls.polySide == 6.0 && pp1.length == 6 && pp2.length == 6) {
      console.log("Cluster marking completed");
      segmentRegions(2,6);
    }
    else if (guiControls.polySide == 7.0 && pp1.length == 7 && pp2.length == 7) {
      console.log("Cluster marking completed");
      segmentRegions(2,7);
    }
    else if (guiControls.polySide == 8.0 && pp1.length == 8 && pp2.length == 8) {
      console.log("Cluster marking completed");
      segmentRegions(2,8);
    }
    else{
      guiControls.clusterMarkingComplete = 0.0;
    }
  }
  else if (guiControls.clusters == 3.0){
    // console.log("Do check");
    console.log(pp1.length, pp2.length, pp3.length);
    if (guiControls.polySide == 5.0 && pp1.length == 5 && pp2.length == 5 && pp3.length == 5) {
      console.log("Cluster marking completed");
      segmentRegions(3,5);
    }
    else if (guiControls.polySide == 6.0 && pp1.length == 6 && pp2.length == 6 && pp3.length == 6) {
      console.log("Cluster marking completed");
      segmentRegions(3,6);
    }
    else if (guiControls.polySide == 7.0 && pp1.length == 7 && pp2.length == 7 && pp3.length == 7) {
      console.log("Cluster marking completed");
      segmentRegions(3,7);
    }
    else if (guiControls.polySide == 8.0 && pp1.length == 8 && pp2.length == 8 && pp3.length == 8) {
      console.log("Cluster marking completed");
      segmentRegions(3,8);
    }
    else{
      guiControls.clusterMarkingComplete = 0.0;
    }
  }
  else if (guiControls.clusters == 4.0){
    // console.log("Do check");
    console.log(pp1.length, pp2.length, pp3.length, pp4.length);
    if (guiControls.polySide == 5.0 && pp1.length == 5 && pp2.length == 5 && pp3.length == 5 && pp4.length == 5) {
      console.log("Cluster marking completed");
      segmentRegions(4,5);
    }
    else if (guiControls.polySide == 6.0 && pp1.length == 6 && pp2.length == 6 && pp3.length == 6 && pp4.length == 6) {
      console.log("Cluster marking completed");
      segmentRegions(4,6);
    }
    else if (guiControls.polySide == 7.0 && pp1.length == 7 && pp2.length == 7 && pp3.length == 7 && pp4.length == 7) {
      console.log("Cluster marking completed");
      segmentRegions(4,7);
    }
    else if (guiControls.polySide == 8.0 && pp1.length == 8 && pp2.length == 8 && pp3.length == 8 && pp4.length == 8) {
      console.log("Cluster marking completed");
      segmentRegions(4,8);
    }
    else{
      guiControls.clusterMarkingComplete = 0.0;
    }
  }
  else if (guiControls.clusters == 5.0){
    // console.log("Do check");
    console.log(pp1.length, pp2.length, pp3.length, pp4.length, pp5.length);
    if (guiControls.polySide == 5.0 && pp1.length == 5 && pp2.length == 5 && pp3.length == 5 && pp4.length == 5 && pp5.length == 5) {
      console.log("Cluster marking completed");
      segmentRegions(5,5);
    }
    else if (guiControls.polySide == 6.0 && pp1.length == 6 && pp2.length == 6 && pp3.length == 6 && pp4.length == 6 && pp5.length == 6) {
      console.log("Cluster marking completed");
      segmentRegions(5,6);
    }
    else if (guiControls.polySide == 7.0 && pp1.length == 7 && pp2.length == 7 && pp3.length == 7 && pp4.length == 7 && pp5.length == 7) {
      console.log("Cluster marking completed");
      segmentRegions(5,7);
    }
    else if (guiControls.polySide == 8.0 && pp1.length == 8 && pp2.length == 8 && pp3.length == 8 && pp4.length == 8 && pp5.length == 8) {
      console.log("Cluster marking completed");
      segmentRegions(5,8);
    }
    else{
      guiControls.clusterMarkingComplete = 0.0;
    }
  }
}

// Get GBC feature space coordinates from the volume voxel values
function getGBCCoords(elementArray) {
  var n = elementArray.length;

  var angle = new Array(n)
  angle[0] = Math.PI / 2 + guiControls.rotateVar3D / 57.32;

  var GBCXL = 0.0;
  var GBCYL = 0.0;

  // Create new array of shape(n, 2)
  var GBCX = new Array(n);
  var GBCY = new Array(n);

  GBCX[0] = Math.cos(angle[0]);
  GBCY[0] = Math.sin(angle[0]);

  for (var i = 1; i < n; i++) {
    angle[i] = angle[i - 1] - 2 * Math.PI / n;
    GBCX[i] = Math.cos(angle[i]) * 0.997;
    GBCY[i] = Math.sin(angle[i]) * 0.997;
  }

  for (var i = 0; i < n; i++) {
    if (angle[i] < 0) {
        angle[i] = angle[i] + Math.PI * 2;
    }
    if (angle[i] > Math.PI * 2) {
        angle[i] = angle[i] - Math.PI * 2;
    }
  }

  angle.sort();

  var tempsumXY = 0;
  // Add all the metal ratios for the voxel
  for (var j = 0; j < n; j++) {
    tempsumXY = tempsumXY + parseFloat(elementArray[j]);
  }

  // If the sum of the metal ratios is 0, set the first 2 dimensions to 0
  if (tempsumXY == 0) {
    GBCXL = 0.0;
    GBCYL = 0.0;
  }

  // Else, calculate the first 2 dimensions based on the metal ratios
  else {
    for (var k = 0; k < n; k++) {
      GBCXL = GBCXL + (elementArray[k] / tempsumXY) * GBCX[k];
      GBCYL = GBCYL + (elementArray[k] / tempsumXY) * GBCY[k];
    }

    var tempangleXY = Math.atan2(GBCYL, GBCXL);

    if (tempangleXY < 0) { 
      tempangleXY = tempangleXY + Math.PI * 2; 
    }

    var flag = false;
    var tempA = 0;
    var tempB = 0;

    for (var j = 0; j < n - 1; j++) {
      if ((tempangleXY > angle[j] || tempangleXY == angle[j]) && (tempangleXY < angle[j + 1])) {
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

    var lthXY = (Math.sqrt((GBCXL * GBCXL) + (GBCYL * GBCYL)) / Math.cos((tempA - tempB) / 2) * Math.cos(-(tempA + tempB) / 2 + tempangleXY));
    
    GBCXL = (lthXY * Math.cos(tempangleXY));
    GBCYL = (lthXY * Math.sin(tempangleXY));
  }

  let CX = GBCXL;
  let CY = GBCYL;

  // Compute rr
  let rr = Math.sqrt(Math.pow(CX, 2.0) + Math.pow(CY, 2.0));

  // Normalize CX and CY if rr >= 1.0
  if (rr >= 1.0) {
      CX /= rr;
      CY /= rr;
  }

  let newCX = 0.0;
  let newCY = 0.0;

  // Compute newCX and newCY
  newCX = (CX + 1.0) / 2.0 * 310.0 + 45.0;
  newCY = (CY + 1.0) / 2.0 * 310.0 + 45.0;

  return [newCX, newCY];
  
}

// Check if a point is inside a polygon with 4 vertices
function pnpoly4(polyX14, polyY14, testx, testy) {
  let c = false;

  // Check first edge (between point 0 and point 3)
  if (((polyY14[0] > testy) !== (polyY14[3] > testy)) && 
      (testx < (polyX14[3] - polyX14[0]) * (testy - polyY14[3]) / (polyY14[3] - polyY14[0]) + polyX14[0])) {
      c = !c;
  }

  // Loop through the remaining edges (between points i and i-1)
  for (let i = 1; i < 4; i++) {
      if (((polyY14[i] > testy) !== (polyY14[i - 1] > testy)) && 
          (testx < (polyX14[i - 1] - polyX14[i]) * (testy - polyY14[i]) / (polyY14[i - 1] - polyY14[i]) + polyX14[i])) {
          c = !c;
      }
  }

  return c;
}

// Check if a point is inside a polygon with 5 vertices
function pnpoly5(polyX15, polyY15, testx, testy) {
  let c = false;

  // Check first edge (between point 0 and point 4)
  if (((polyY15[0] > testy) !== (polyY15[4] > testy)) &&
      (testx < (polyX15[4] - polyX15[0]) * (testy - polyY15[4]) / (polyY15[4] - polyY15[0]) + polyX15[0])) {
      c = !c;
  }

  // Loop through the remaining edges (between points i and i-1)
  for (let i = 1; i < 5; i++) {
      if (((polyY15[i] > testy) !== (polyY15[i - 1] > testy)) &&
          (testx < (polyX15[i - 1] - polyX15[i]) * (testy - polyY15[i]) / (polyY15[i - 1] - polyY15[i]) + polyX15[i])) {
          c = !c;
      }
  }

  return c;
}

// Check if a point is inside a polygon with 6 vertices
function pnpoly6(polyX16, polyY16, testx, testy) {
  let c = false;

  // Check first edge (between point 0 and point 5)
  if (((polyY16[0] > testy) !== (polyY16[5] > testy)) &&
      (testx < (polyX16[5] - polyX16[0]) * (testy - polyY16[5]) / (polyY16[5] - polyY16[0]) + polyX16[0])) {
      c = !c;
  }

  // Loop through the remaining edges (between points i and i-1)
  for (let i = 1; i < 6; i++) {
      if (((polyY16[i] > testy) !== (polyY16[i - 1] > testy)) &&
          (testx < (polyX16[i - 1] - polyX16[i]) * (testy - polyY16[i]) / (polyY16[i - 1] - polyY16[i]) + polyX16[i])) {
          c = !c;
      }
  }

  return c;
}

// Check if a point is inside a polygon with 7 vertices
function pnpoly7(polyX17, polyY17, testx, testy) {
  let c = false;

  // Check first edge (between point 0 and point 6)
  if (((polyY17[0] > testy) !== (polyY17[6] > testy)) &&
      (testx < (polyX17[6] - polyX17[0]) * (testy - polyY17[6]) / (polyY17[6] - polyY17[0]) + polyX17[0])) {
      c = !c;
  }

  // Loop through the remaining edges (between points i and i-1)
  for (let i = 1; i < 7; i++) {
      if (((polyY17[i] > testy) !== (polyY17[i - 1] > testy)) &&
          (testx < (polyX17[i - 1] - polyX17[i]) * (testy - polyY17[i]) / (polyY17[i - 1] - polyY17[i]) + polyX17[i])) {
          c = !c;
      }
  }

  return c;
}

// Check if voxel in volume is part of any cluster 
function checkPNP(clusterNo, sideNo, newBoundaryArray, testx, testy){
  // Check if voxel is inside any of the clusters for polygon with 4 vertices
  if (sideNo == 5){
    // Store the x and y coordinates of the polygon vertices in separate arrays
    var polyX = [];
    var polyY = [];
    for(var i=0; i<clusterNo; i++){
      polyX[i] = [];
      polyY[i] = [];
      for(var j=0; j<sideNo-1; j++){
        polyX[i].push(newBoundaryArray[i][j][0]);
        polyY[i].push(newBoundaryArray[i][j][1]);
      }
    }

    // Check if voxel is inside any of the clusters
    var pointIO1 = pnpoly4(polyX[0], polyY[0], testx, testy);
    if(pointIO1 == true){
      // console.log("Point inside Cluster 1");
      return 1;
    }
    else if(polyX[1] != undefined){
      var pointIO2 = pnpoly4(polyX[1], polyY[1], testx, testy);
      if(pointIO2 == true){
        // console.log("Point inside Cluster 2");
        return 2;
      }
      else if(polyX[2] != undefined){
        var pointIO3 = pnpoly4(polyX[2], polyY[2], testx, testy);
        if(pointIO3 == true){
          // console.log("Point inside Cluster 3");
          return 3;
        }
        else if(polyX[3] != undefined){
          var pointIO4 = pnpoly4(polyX[3], polyY[3], testx, testy);
          if(pointIO4 == true){
            // console.log("Point inside Cluster 4");
            return 4;
          }
          else if(polyX[4] != undefined){
            var pointIO5 = pnpoly4(polyX[4], polyY[4], testx, testy);
            if(pointIO5 == true){
              // console.log("Point inside Cluster 5");
              return 5;
            }
          }
        }
      }
    }
    // console.log("Point outside all clusters");
    return 0;
  }
  // Check if voxel is inside any of the clusters for polygon with 5 vertices
  else if (sideNo == 6){
    // Store the x and y coordinates of the polygon vertices in separate arrays
    var polyX = [];
    var polyY = [];
    for(var i=0; i<clusterNo; i++){
      polyX[i] = [];
      polyY[i] = [];
      for(var j=0; j<sideNo-1; j++){
        polyX[i].push(newBoundaryArray[i][j][0]);
        polyY[i].push(newBoundaryArray[i][j][1]);
      }
    }

    // Check if voxel is inside any of the clusters
    var pointIO1 = pnpoly5(polyX[0], polyY[0], testx, testy);
    if(pointIO1 == true){
      // console.log("Point inside Cluster 1");
      return 1;
    }
    else if(polyX[1] != undefined){
      var pointIO2 = pnpoly5(polyX[1], polyY[1], testx, testy);
      if(pointIO2 == true){
        // console.log("Point inside Cluster 2");
        return 2;
      }
      else if(polyX[2] != undefined){
        var pointIO3 = pnpoly5(polyX[2], polyY[2], testx, testy);
        if(pointIO3 == true){
          // console.log("Point inside Cluster 3");
          return 3;
        }
        else if(polyX[3] != undefined){
          var pointIO4 = pnpoly5(polyX[3], polyY[3], testx, testy);
          if(pointIO4 == true){
            // console.log("Point inside Cluster 4");
            return 4;
          }
          else if(polyX[4] != undefined){
            var pointIO5 = pnpoly5(polyX[4], polyY[4], testx, testy);
            if(pointIO5 == true){
              // console.log("Point inside Cluster 5");
              return 5;
            }
          }
        }
      }
    }
    // console.log("Point outside all clusters");
    return 0;
  }
  // Check if voxel is inside any of the clusters for polygon with 6 vertices
  else if (sideNo == 7){
    // Store the x and y coordinates of the polygon vertices in separate arrays
    var polyX = [];
    var polyY = [];
    for(var i=0; i<clusterNo; i++){
      polyX[i] = [];
      polyY[i] = [];
      for(var j=0; j<sideNo-1; j++){
        polyX[i].push(newBoundaryArray[i][j][0]);
        polyY[i].push(newBoundaryArray[i][j][1]);
      }
    }

    // Check if voxel is inside any of the clusters
    var pointIO1 = pnpoly6(polyX[0], polyY[0], testx, testy);
    if(pointIO1 == true){
      // console.log("Point inside Cluster 1");
      return 1;
    }
    else if(polyX[1] != undefined){
      var pointIO2 = pnpoly6(polyX[1], polyY[1], testx, testy);
      if(pointIO2 == true){
        // console.log("Point inside Cluster 2");
        return 2;
      }
      else if(polyX[2] != undefined){
        var pointIO3 = pnpoly6(polyX[2], polyY[2], testx, testy);
        if(pointIO3 == true){
          // console.log("Point inside Cluster 3");
          return 3;
        }
        else if(polyX[3] != undefined){
          var pointIO4 = pnpoly6(polyX[3], polyY[3], testx, testy);
          if(pointIO4 == true){
            // console.log("Point inside Cluster 4");
            return 4;
          }
          else if(polyX[4] != undefined){
            var pointIO5 = pnpoly6(polyX[4], polyY[4], testx, testy);
            if(pointIO5 == true){
              // console.log("Point inside Cluster 5");
              return 5;
            }
          }
        }
      }
    }
    // console.log("Point outside all clusters");
    return 0;
  }
  // Check if voxel is inside any of the clusters for polygon with 7 vertices
  else if (sideNo == 8){
    // Store the x and y coordinates of the polygon vertices in separate arrays
    var polyX = [];
    var polyY = [];
    for(var i=0; i<clusterNo; i++){
      polyX[i] = [];
      polyY[i] = [];
      for(var j=0; j<sideNo-1; j++){
        polyX[i].push(newBoundaryArray[i][j][0]);
        polyY[i].push(newBoundaryArray[i][j][1]);
      }
    }

    // Check if voxel is inside any of the clusters
    var pointIO1 = pnpoly7(polyX[0], polyY[0], testx, testy);
    if(pointIO1 == true){
      // console.log("Point inside Cluster 1");
      return 1;
    }
    else if(polyX[1] != undefined){
      var pointIO2 = pnpoly7(polyX[1], polyY[1], testx, testy);
      if(pointIO2 == true){
        // console.log("Point inside Cluster 2");
        return 2;
      }
      else if(polyX[2] != undefined){
        var pointIO3 = pnpoly7(polyX[2], polyY[2], testx, testy);
        if(pointIO3 == true){
          // console.log("Point inside Cluster 3");
          return 3;
        }
        else if(polyX[3] != undefined){
          var pointIO4 = pnpoly7(polyX[3], polyY[3], testx, testy);
          if(pointIO4 == true){
            // console.log("Point inside Cluster 4");
            return 4;
          }
          else if(polyX[4] != undefined){
            var pointIO5 = pnpoly7(polyX[4], polyY[4], testx, testy);
            if(pointIO5 == true){
              // console.log("Point inside Cluster 5");
              return 5;
            }
          }
        }
      }
    }
    // console.log("Point outside all clusters");
    return 0;
  }
}

// Function to create array of 2D textures from 3D volume data
function create2dTextures(volumeData){
  console.log(volumeData);
  const volumeWidth = volumeData.length;        // X dimension
  const volumeHeight = volumeData[0].length;    // Y dimension
  const volumeDepth = volumeData[0][0].length;  // Z dimension

  // Create a 2D texture by packing 3D data into slices of a 2D texture
  const textureSize = volumeWidth * volumeDepth;
  const textureData = new Uint8Array(textureSize * volumeHeight * 4); // RGBA texture

  // console.log(textureData);
  // Pack the 3D volume data into the 2D texture
  for (let z = 0; z < volumeDepth; z++) {
    for (let y = 0; y < volumeHeight; y++) {
      for (let x = 0; x < volumeWidth; x++) {
        const clusterId = volumeData[x][y][z]; // Access your volumeData
        
        // const textureIndex = (x + z * volumeWidth + y * textureSize) * 4; // Index in 2D texture
        const textureIndex = (x + y * volumeWidth + z * volumeWidth * volumeHeight) * 4;
  
        textureData[textureIndex] = clusterId;   // Store cluster ID in Red channel
        textureData[textureIndex + 1] = 0;       // Unused
        textureData[textureIndex + 2] = 0;       // Unused
        textureData[textureIndex + 3] = 255;     // Full alpha
      }
    }
  }

  console.log(textureData);

  // Find the number of unique values in the volume
  const uniqueValues = new Set(textureData);
  console.log(uniqueValues);

  // Find index of first occurrence of a value in the texture data
  // const firstIndex = textureData.indexOf(1);
  // console.log(firstIndex);

  // Create a WebGL texture from the packed 2D texture data
  window.volumeTexture = new THREE.DataTexture(
    textureData,
    textureSize,
    volumeHeight,
    THREE.RGBAFormat,
    THREE.UnsignedByteType
  );
  window.volumeTexture.needsUpdate = true;
  window.volumeTexture.generateMipmaps = false;
  window.volumeTexture.minFilter = THREE.NearestFilter;
  window.volumeTexture.magFilter = THREE.NearestFilter;

  console.log(window.volumeTexture);  // Verify the contents

  guiControls.clusterMarkingComplete = 1.0;
}

function create2dTextures1(volumeData) {
  const volumeWidth = volumeData.length;        // X dimension (256)
  const volumeHeight = volumeData[0].length;    // Y dimension (256)
  const volumeDepth = volumeData[0][0].length;  // Z dimension (256)

  const gridSize = Math.ceil(Math.sqrt(volumeDepth)); // 16 for 256 slices
  const textureSize = volumeWidth * gridSize;         // 256 * 16 = 4096
  const textureData = new Uint8Array(textureSize * textureSize * 4); // RGBA texture

  // Pack the 3D volume data into a 2D texture (16x16 grid of Z-slices)
  for (let z = 0; z < volumeDepth; z++) {
    const gridX = z % gridSize;
    const gridY = Math.floor(z / gridSize);

    for (let y = 0; y < volumeHeight; y++) {
      for (let x = 0; x < volumeWidth; x++) {
        const clusterId = volumeData[x][y][z]; // Access your volumeData

        // Calculate 2D texture index for the slice in the grid
        const textureX = gridX * volumeWidth + x;
        const textureY = gridY * volumeHeight + y;
        const textureIndex = (textureX + textureY * textureSize) * 4; // RGBA index

        textureData[textureIndex] = clusterId;   // Store cluster ID in Red channel
        textureData[textureIndex + 1] = 0;       // Unused
        textureData[textureIndex + 2] = 0;       // Unused
        textureData[textureIndex + 3] = 255;     // Full alpha
      }
    }
  }

  console.log(textureData);

  // Find the number of unique values in the volume
  const uniqueValues = new Set(textureData);
  console.log(uniqueValues);

  // Find the number of 1s in the volume
  const countOnes = textureData.filter(value => value === 1).length;
  console.log(countOnes);

  // Create the 2D texture in WebGL
  window.volumeTexture = new THREE.DataTexture(
    textureData,
    textureSize,
    textureSize,
    THREE.RGBAFormat,
    THREE.UnsignedByteType
  );
  window.volumeTexture.needsUpdate = true;
  window.volumeTexture.generateMipmaps = false;
  window.volumeTexture.minFilter = THREE.NearestFilter;
  window.volumeTexture.magFilter = THREE.NearestFilter;

  console.log(window.volumeTexture);  // Verify the contents

  guiControls.clusterMarkingComplete = 1.0;

  saveTexture = false;

  // Save the 2D texture to a png file
  if (saveTexture) {
    const canvas = document.createElement('canvas');
    canvas.width = textureSize;
    canvas.height = textureSize;
    const context = canvas.getContext('2d');
    const imageData = context.createImageData(textureSize, textureSize);
    imageData.data.set(textureData);
    context.putImageData(imageData, 0, 0);

    const image = canvas.toDataURL('image/png');
    const a = document.createElement('a');
    a.href = image;
    a.download = '2DTexture.png';
    a.click();
  }
  
}

// Implement rehgion growing algorithm on volume in here
function segmentRegions(clusterNo, sideNo) {
  if (guiControls.clusterMarkingComplete == 1.0) {
    return;
  }
  console.log("Segmenting Regions");
  // console.log(window.npArray.data); // This is your volume data as a typed array
  // console.log(window.npArray.shape); // Shape of the numpy array

  // Find number of unique values in the volume
  // const uniqueValues = new Set(window.npArray.data);
  // console.log(uniqueValues.size);

  // Find the minimum and maximum values in the volume
  // const min = window.npArray.data.reduce((acc, val) => Math.min(acc, val), Infinity);
  // const max = window.npArray.data.reduce((acc, val) => Math.max(acc, val), -Infinity);
  // console.log(min, max);

  const shape = window.npArray.shape;  // [d1, d2, d3, d4]
  const data = window.npArray.data;    // TypedArray with flattened data

  // Access elements at indices [100, 100, 100]
  // const value1 = getElement(data, shape, [100, 100, 100, 0]);
  // const value2 = getElement(data, shape, [100, 100, 100, 1]);
  // const value3 = getElement(data, shape, [100, 100, 100, 2]);
  // const value4 = getElement(data, shape, [100, 100, 100, 3]);
  // console.log(value1, value2, value3, value4);

  // Get the GBC feature space coordinates corresponding to the volume coordinates
  var voxelGBCArray = [];
  var elementArray = new Array(shape[3]);
  
  // Loop through the volume data to get the GBC feature space coordinates corresponding to each voxel of the volume data
  for(i=0; i<shape[0]; i++){
    voxelGBCArray[i] = [];

    for(j=0; j<shape[1]; j++){
      voxelGBCArray[i][j] = [];

      for(k=0; k<shape[2]; k++){
        voxelGBCArray[i][j][k] = [];
        isNanValue = false;

        for(l=0; l<shape[3]; l++){
          element = getElement(data, shape, [i, j, k, l]);

          // Check if element is NaN
          if(isNaN(element)){
            isNanValue = true;
            break;
          }

          else{
            elementArray[l] = element;
          }
        }

        // return x and y coordinates of the GBC feature space
        if(isNanValue == false){
          voxelGBCArray[i][j][k] = getGBCCoords(elementArray).concat(elementArray);
        }
        // If NaN value is present, assign 0 to the x and y coordinates
        else{
          voxelGBCArray[i][j][k] = [0, 0];
        }
      }
    }
  }

  // console.log(voxelGBCArray);
  console.log("GBC feature space coordinates extracted");

  // ----------------------------------------------------------------------------------------------------

  // Load marked boundary coordinates to array
  var boundaryArray = [];
  for(i=0; i<clusterNo; i++){
    var tempArray = [];
    for(j=0; j<sideNo; j++){
      var tempCoord = [];
      if(i==0){
        tempCoord.push(guiControls['x'+(j+1)]);
        tempCoord.push(guiControls['y'+(j+1)]);
      }
      else if(i==1){
        tempCoord.push(guiControls['x1'+(j+1)]);
        tempCoord.push(guiControls['y1'+(j+1)]);
      }
      else if(i==2){
        tempCoord.push(guiControls['x3'+(j+1)]);
        tempCoord.push(guiControls['y3'+(j+1)]);
      }
      else if(i==3){
        tempCoord.push(guiControls['x4'+(j+1)]);
        tempCoord.push(guiControls['y4'+(j+1)]);
      }
      else if(i==4){
        tempCoord.push(guiControls['x5'+(j+1)]);
        tempCoord.push(guiControls['y5'+(j+1)]);
      }
      tempArray.push(tempCoord);
    }
    boundaryArray.push(tempArray);
  }
  // console.log(boundaryArray);

  // ----------------------------------------------------------------------------------------------------
  // Inverse scaling of coordinates to get back GBC feature space coordinates (Not required for now)

  // var colorSpaceWidth = 400;//document.getElementById(this.iconColorSpaceContainerId).clientWidth;
  // var colorSpaceHeight = 400;//this.colorSpaceWidth;
  // var diameter = Math.round(colorSpaceHeight * 2.4 / 3.1);
  // var xoffset = (colorSpaceWidth - diameter) / 2;
  // var scaleGBC2Canvas = d3.scale.linear().domain([-1, 1]).range([xoffset, xoffset + diameter]);

  // newBoundaryArray = [];
  // for(var i=0; i<clusterNo; i++){
  //   newBoundaryArray[i] = [];
  //   for(var j=0; j<sideNo; j++){
  //     newBoundaryArray[i][j] = [];
  //     newBoundaryArray[i][j][0] = scaleGBC2Canvas.invert(boundaryArray[i][j][0]);
  //     newBoundaryArray[i][j][1] = scaleGBC2Canvas.invert(boundaryArray[i][j][1]);
  //   }
  // }
  // console.log(newBoundaryArray);

  // ----------------------------------------------------------------------------------------------------
  
  // Call PNP algorithm function here
  console.log("Call PNP function");
  for(var i=0; i<shape[0]; i++){
    for(var j=0; j<shape[1]; j++){
      for(var k=0; k<shape[2]; k++){
        var testx = voxelGBCArray[i][j][k][0];
        var testy = voxelGBCArray[i][j][k][1];
        // Process the NaN values present in the volume data
        if (testx == 0 && testy == 0){
          // Assign them as outlier since cant perform region growing on them (50 is a random number which is not a cluster number just to differentiate)
          voxelGBCArray[i][j][k].push(50);
        }
        // Process the non-NaN values present in the volume data to assign them a cluster
        else{
          // pointInCluster = checkPNP(clusterNo, sideNo, newBoundaryArray, testx, testy);
          pointInCluster = checkPNP(clusterNo, sideNo, boundaryArray, testx, testy);
          voxelGBCArray[i][j][k].push(pointInCluster);
        }
      }
    }
  }
  // console.log(voxelGBCArray);
  console.log("All points clustered");

  // Save the clustered data to a file
  var clusterData = [];
  for(var i=0; i<shape[0]; i++){
    clusterData[i] = [];
    for(var j=0; j<shape[1]; j++){
      clusterData[i][j] = [];
      for(var k=0; k<shape[2]; k++){
        clusterData[i][j][k] = voxelGBCArray[i][j][k].at(-1);
      }
    }
  }
  console.log("Done extracting cluster data");
  // console.log(clusterData);

  let saveCLusterData = false;

  if (saveCLusterData) {
    // Convert the 3D array to a JSON string
    // let arrayStr = JSON.stringify(clusterData);
    let arrayStr = JSON.stringify(voxelGBCArray);
    console.log("Conversion done");

    // Save the data to a file
    var blob = new Blob([arrayStr], {type: "application/json"});
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'clusteredDataRatio4.json';
    a.click();
  }

  // ----------------------------------------------------------------------------------------------------

  // Function to create array of 2D textures from 3D volume data
  create2dTextures1(clusterData)
  console.log("Textures created");
}