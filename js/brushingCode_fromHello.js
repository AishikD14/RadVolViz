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
      console.log("drawpoly")
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
      guiControls.x2 = pp1[1][0];
      guiControls.x3 = pp1[2][0];
      guiControls.x4 = pp1[3][0];
      guiControls.x5 = pp1[4][0];

      guiControls.y1 = pp1[0][1];
      guiControls.y2 = pp1[1][1];
      guiControls.y3 = pp1[2][1];
      guiControls.y4 = pp1[3][1];
      guiControls.y5 = pp1[4][1];

    }

    if (pp2.length > 0) {
      guiControls.x11 = pp2[0][0];
      guiControls.x12 = pp2[1][0];
      guiControls.x13 = pp2[2][0];
      guiControls.x14 = pp2[3][0];
      guiControls.x15 = pp2[4][0];
      
      guiControls.y11 = pp2[0][1];
      guiControls.y12 = pp2[1][1];
      guiControls.y13 = pp2[2][1];
      guiControls.y14 = pp2[3][1];
      guiControls.y15 = pp2[4][1];
    }

    if (pp3.length > 0) {
      guiControls.x31 = pp3[0][0];
      guiControls.x32 = pp3[1][0];
      guiControls.x33 = pp3[2][0];
      guiControls.x34 = pp3[3][0];
      guiControls.x35 = pp3[4][0];

      guiControls.y31 = pp3[0][1];
      guiControls.y32 = pp3[1][1];
      guiControls.y33 = pp3[2][1];
      guiControls.y34 = pp3[3][1];
      guiControls.y35 = pp3[4][1];
    }

    if (pp4.length > 0) {
      guiControls.x41 = pp4[0][0];
      guiControls.x42 = pp4[1][0];
      guiControls.x43 = pp4[2][0];
      guiControls.x44 = pp4[3][0];
      guiControls.x45 = pp4[4][0];

      guiControls.y41 = pp4[0][1];
      guiControls.y42 = pp4[1][1];
      guiControls.y43 = pp4[2][1];
      guiControls.y44 = pp4[3][1];
      guiControls.y45 = pp4[4][1];
    }

    if (pp5.length > 0) {
      guiControls.x51 = pp5[0][0];
      guiControls.x52 = pp5[1][0];
      guiControls.x53 = pp5[2][0];
      guiControls.x54 = pp5[3][0];
      guiControls.x55 = pp5[4][0];

      guiControls.y51 = pp5[0][1];
      guiControls.y52 = pp5[1][1];
      guiControls.y53 = pp5[2][1];
      guiControls.y54 = pp5[3][1];
      guiControls.y55 = pp5[4][1];
    }

  }

  if (guiControls.polySide == 6.0) {

    if (pp1.length > 0) {
      guiControls.x1 = pp1[0][0];
      guiControls.x2 = pp1[1][0];
      guiControls.x3 = pp1[2][0];
      guiControls.x4 = pp1[3][0];
      guiControls.x5 = pp1[4][0];
      guiControls.x6 = pp1[5][0];

      guiControls.y1 = pp1[0][1];
      guiControls.y2 = pp1[1][1];
      guiControls.y3 = pp1[2][1];
      guiControls.y4 = pp1[3][1];
      guiControls.y5 = pp1[4][1];
      guiControls.y6 = pp1[5][1];
    }

    if (pp2.length > 0) {
      guiControls.x11 = pp2[0][0];
      guiControls.x12 = pp2[1][0];
      guiControls.x13 = pp2[2][0];
      guiControls.x14 = pp2[3][0];
      guiControls.x15 = pp2[4][0];
      guiControls.x16 = pp2[5][0];

      guiControls.y11 = pp2[0][1];
      guiControls.y12 = pp2[1][1];
      guiControls.y13 = pp2[2][1];
      guiControls.y14 = pp2[3][1];
      guiControls.y15 = pp2[4][1];
      guiControls.y16 = pp2[5][1];

      // Can delete if needed
      // guiControls.x11 = pp2[1][0];
      // guiControls.x12 = pp2[2][0];
      // guiControls.x13 = pp2[3][0];
      // guiControls.x14 = pp2[4][0];
      // guiControls.x15 = pp2[5][0];
      // guiControls.x16 = pp2[6][0];

      // guiControls.y11 = pp2[1][1];
      // guiControls.y12 = pp2[2][1];
      // guiControls.y13 = pp2[3][1];
      // guiControls.y14 = pp2[4][1];
      // guiControls.y15 = pp2[5][1];
      // guiControls.y16 = pp2[6][1];
    }

    if (pp3.length > 0) {
      guiControls.x31 = pp3[0][0];
      guiControls.x32 = pp3[1][0];
      guiControls.x33 = pp3[2][0];
      guiControls.x34 = pp3[3][0];
      guiControls.x35 = pp3[4][0];
      guiControls.x36 = pp3[5][0];

      guiControls.y31 = pp3[0][1];
      guiControls.y32 = pp3[1][1];
      guiControls.y33 = pp3[2][1];
      guiControls.y34 = pp3[3][1];
      guiControls.y35 = pp3[4][1];
      guiControls.y36 = pp3[5][1];

      // Can delete if needed
      // guiControls.x31 = pp3[1][0];
      // guiControls.x32 = pp3[2][0];
      // guiControls.x33 = pp3[3][0];
      // guiControls.x34 = pp3[4][0];
      // guiControls.x35 = pp3[5][0];
      // guiControls.x36 = pp3[6][0];

      // guiControls.y31 = pp3[1][1];
      // guiControls.y32 = pp3[2][1];
      // guiControls.y33 = pp3[3][1];
      // guiControls.y34 = pp3[4][1];
      // guiControls.y35 = pp3[5][1];
      // guiControls.y36 = pp3[6][1];
    }

    if (pp4.length > 0) {
      guiControls.x41 = pp4[0][0];
      guiControls.x42 = pp4[1][0];
      guiControls.x43 = pp4[2][0];
      guiControls.x44 = pp4[3][0];
      guiControls.x45 = pp4[4][0];
      guiControls.x46 = pp4[5][0];

      guiControls.y41 = pp4[0][1];
      guiControls.y42 = pp4[1][1];
      guiControls.y43 = pp4[2][1];
      guiControls.y44 = pp4[3][1];
      guiControls.y45 = pp4[4][1];
      guiControls.y46 = pp4[5][1];

      // Can delete if needed
      // guiControls.x41 = pp4[1][0];
      // guiControls.x42 = pp4[2][0];
      // guiControls.x43 = pp4[3][0];
      // guiControls.x44 = pp4[4][0];
      // guiControls.x45 = pp4[5][0];
      // guiControls.x46 = pp4[6][0];

      // guiControls.y41 = pp4[1][1];
      // guiControls.y42 = pp4[2][1];
      // guiControls.y43 = pp4[3][1];
      // guiControls.y44 = pp4[4][1];
      // guiControls.y45 = pp4[5][1];
      // guiControls.y46 = pp4[6][1];
    }

    if (pp5.length > 0) {
      guiControls.x51 = pp5[0][0];
      guiControls.x52 = pp5[1][0];
      guiControls.x53 = pp5[2][0];
      guiControls.x54 = pp5[3][0];
      guiControls.x55 = pp5[4][0];
      guiControls.x56 = pp5[5][0];

      guiControls.y51 = pp5[0][1];
      guiControls.y52 = pp5[1][1];
      guiControls.y53 = pp5[2][1];
      guiControls.y54 = pp5[3][1];
      guiControls.y55 = pp5[4][1];
      guiControls.y56 = pp5[5][1];

      // Can delete if needed
      // guiControls.x51 = pp5[1][0];
      // guiControls.x52 = pp5[2][0];
      // guiControls.x53 = pp5[3][0];
      // guiControls.x54 = pp5[4][0];
      // guiControls.x55 = pp5[5][0];
      // guiControls.x56 = pp5[6][0];

      // guiControls.y51 = pp5[1][1];
      // guiControls.y52 = pp5[2][1];
      // guiControls.y53 = pp5[3][1];
      // guiControls.y54 = pp5[4][1];
      // guiControls.y55 = pp5[5][1];
      // guiControls.y56 = pp5[6][1];
    }
  }

  if (guiControls.polySide == 7.0) {
    if (pp1.length > 0) {
      guiControls.x1 = pp1[0][0];
      guiControls.x2 = pp1[1][0];
      guiControls.x3 = pp1[2][0];
      guiControls.x4 = pp1[3][0];
      guiControls.x5 = pp1[4][0];
      guiControls.x6 = pp1[5][0];
      guiControls.x7 = pp1[6][0];

      guiControls.y1 = pp1[0][1];
      guiControls.y2 = pp1[1][1];
      guiControls.y3 = pp1[2][1];
      guiControls.y4 = pp1[3][1];
      guiControls.y5 = pp1[4][1];
      guiControls.y6 = pp1[5][1];
      guiControls.y7 = pp1[6][1];
    }

    if (pp2.length > 0) {
      guiControls.x11 = pp2[0][0];
      guiControls.x12 = pp2[1][0];
      guiControls.x13 = pp2[2][0];
      guiControls.x14 = pp2[3][0];
      guiControls.x15 = pp2[4][0];
      guiControls.x16 = pp2[5][0];
      guiControls.x17 = pp2[6][0];

      guiControls.y11 = pp2[0][1];
      guiControls.y12 = pp2[1][1];
      guiControls.y13 = pp2[2][1];
      guiControls.y14 = pp2[3][1];
      guiControls.y15 = pp2[4][1];
      guiControls.y16 = pp2[5][1];
      guiControls.y17 = pp2[6][1];

      // Can delete if needed
      // guiControls.x11 = pp2[1][0];
      // guiControls.x12 = pp2[2][0];
      // guiControls.x13 = pp2[3][0];
      // guiControls.x14 = pp2[4][0];
      // guiControls.x15 = pp2[5][0];
      // guiControls.x16 = pp2[6][0];
      // guiControls.x17 = pp2[7][0];

      // guiControls.y11 = pp2[1][1];
      // guiControls.y12 = pp2[2][1];
      // guiControls.y13 = pp2[3][1];
      // guiControls.y14 = pp2[4][1];
      // guiControls.y15 = pp2[5][1];
      // guiControls.y16 = pp2[6][1];
      // guiControls.y17 = pp2[7][1];
    }

    if (pp3.length > 0) {
      guiControls.x31 = pp3[0][0];
      guiControls.x32 = pp3[1][0];
      guiControls.x33 = pp3[2][0];
      guiControls.x34 = pp3[3][0];
      guiControls.x35 = pp3[4][0];
      guiControls.x36 = pp3[5][0];
      guiControls.x37 = pp3[6][0];

      guiControls.y31 = pp3[0][1];
      guiControls.y32 = pp3[1][1];
      guiControls.y33 = pp3[2][1];
      guiControls.y34 = pp3[3][1];
      guiControls.y35 = pp3[4][1];
      guiControls.y36 = pp3[5][1];
      guiControls.y37 = pp3[6][1];

      // Can delete if needed
      // guiControls.x31 = pp3[1][0];
      // guiControls.x32 = pp3[2][0];
      // guiControls.x33 = pp3[3][0];
      // guiControls.x34 = pp3[4][0];
      // guiControls.x35 = pp3[5][0];
      // guiControls.x36 = pp3[6][0];
      // guiControls.x37 = pp3[7][0];

      // guiControls.y31 = pp3[1][1];
      // guiControls.y32 = pp3[2][1];
      // guiControls.y33 = pp3[3][1];
      // guiControls.y34 = pp3[4][1];
      // guiControls.y35 = pp3[5][1];
      // guiControls.y36 = pp3[6][1];
      // guiControls.y37 = pp3[7][1];
    }

    if (pp4.length > 0) {
      guiControls.x41 = pp4[0][0];
      guiControls.x42 = pp4[1][0];
      guiControls.x43 = pp4[2][0];
      guiControls.x44 = pp4[3][0];
      guiControls.x45 = pp4[4][0];
      guiControls.x46 = pp4[5][0];
      guiControls.x47 = pp4[6][0];

      guiControls.y41 = pp4[0][1];
      guiControls.y42 = pp4[1][1];
      guiControls.y43 = pp4[2][1];
      guiControls.y44 = pp4[3][1];
      guiControls.y45 = pp4[4][1];
      guiControls.y46 = pp4[5][1];
      guiControls.y47 = pp4[6][1];

      // Can delete if needed
      // guiControls.x41 = pp4[1][0];
      // guiControls.x42 = pp4[2][0];
      // guiControls.x43 = pp4[3][0];
      // guiControls.x44 = pp4[4][0];
      // guiControls.x45 = pp4[5][0];
      // guiControls.x46 = pp4[6][0];
      // guiControls.x47 = pp4[7][0];

      // guiControls.y41 = pp4[1][1];
      // guiControls.y42 = pp4[2][1];
      // guiControls.y43 = pp4[3][1];
      // guiControls.y44 = pp4[4][1];
      // guiControls.y45 = pp4[5][1];
      // guiControls.y46 = pp4[6][1];
      // guiControls.y47 = pp4[7][1];
    }

    if (pp5.length > 0) {
      guiControls.x51 = pp5[0][0];
      guiControls.x52 = pp5[1][0];
      guiControls.x53 = pp5[2][0];
      guiControls.x54 = pp5[3][0];
      guiControls.x55 = pp5[4][0];
      guiControls.x56 = pp5[5][0];
      guiControls.x57 = pp5[6][0];

      guiControls.y51 = pp5[0][1];
      guiControls.y52 = pp5[1][1];
      guiControls.y53 = pp5[2][1];
      guiControls.y54 = pp5[3][1];
      guiControls.y55 = pp5[4][1];
      guiControls.y56 = pp5[5][1];
      guiControls.y57 = pp5[6][1];

      // Can delete if needed
      // guiControls.x51 = pp5[1][0];
      // guiControls.x52 = pp5[2][0];
      // guiControls.x53 = pp5[3][0];
      // guiControls.x54 = pp5[4][0];
      // guiControls.x55 = pp5[5][0];
      // guiControls.x56 = pp5[6][0];
      // guiControls.x57 = pp5[7][0];

      // guiControls.y51 = pp5[1][1];
      // guiControls.y52 = pp5[2][1];
      // guiControls.y53 = pp5[3][1];
      // guiControls.y54 = pp5[4][1];
      // guiControls.y55 = pp5[5][1];
      // guiControls.y56 = pp5[6][1];
      // guiControls.y57 = pp5[7][1];
    }
  }

  if (guiControls.polySide == 8.0) {
    if (pp1.length > 0) {
      guiControls.x1 = pp1[0][0];
      guiControls.x2 = pp1[1][0];
      guiControls.x3 = pp1[2][0];
      guiControls.x4 = pp1[3][0];
      guiControls.x5 = pp1[4][0];
      guiControls.x6 = pp1[5][0];
      guiControls.x7 = pp1[6][0];
      guiControls.x8 = pp1[7][0];

      guiControls.y1 = pp1[0][1];
      guiControls.y2 = pp1[1][1];
      guiControls.y3 = pp1[2][1];
      guiControls.y4 = pp1[3][1];
      guiControls.y5 = pp1[4][1];
      guiControls.y6 = pp1[5][1];
      guiControls.y7 = pp1[6][1];
      guiControls.x8 = pp1[7][0];
    }

    if (pp2.length > 0) {
      guiControls.x11 = pp2[0][0];
      guiControls.x12 = pp2[1][0];
      guiControls.x13 = pp2[2][0];
      guiControls.x14 = pp2[3][0];
      guiControls.x15 = pp2[4][0];
      guiControls.x16 = pp2[5][0];
      guiControls.x17 = pp2[6][0];
      guiControls.x18 = pp2[7][0];

      guiControls.y11 = pp2[0][1];
      guiControls.y12 = pp2[1][1];
      guiControls.y13 = pp2[2][1];
      guiControls.y14 = pp2[3][1];
      guiControls.y15 = pp2[4][1];
      guiControls.y16 = pp2[5][1];
      guiControls.y17 = pp2[6][1];
      guiControls.y18 = pp2[7][1];
    }

    if (pp3.length > 0) {
      guiControls.x31 = pp3[0][0];
      guiControls.x32 = pp3[1][0];
      guiControls.x33 = pp3[2][0];
      guiControls.x34 = pp3[3][0];
      guiControls.x35 = pp3[4][0];
      guiControls.x36 = pp3[5][0];
      guiControls.x37 = pp3[6][0];
      guiControls.x38 = pp3[7][0];

      guiControls.y31 = pp3[0][1];
      guiControls.y32 = pp3[1][1];
      guiControls.y33 = pp3[2][1];
      guiControls.y34 = pp3[3][1];
      guiControls.y35 = pp3[4][1];
      guiControls.y36 = pp3[5][1];
      guiControls.y37 = pp3[6][1];
      guiControls.y38 = pp3[7][1];

      // Can delete if needed
      // guiControls.x31 = pp3[1][0];
      // guiControls.x32 = pp3[2][0];
      // guiControls.x33 = pp3[3][0];
      // guiControls.x34 = pp3[4][0];
      // guiControls.x35 = pp3[5][0];
      // guiControls.x36 = pp3[6][0];
      // guiControls.x37 = pp3[7][0];
      // guiControls.x38 = pp3[8][0];

      // guiControls.y31 = pp3[1][1];
      // guiControls.y32 = pp3[2][1];
      // guiControls.y33 = pp3[3][1];
      // guiControls.y34 = pp3[4][1];
      // guiControls.y35 = pp3[5][1];
      // guiControls.y36 = pp3[6][1];
      // guiControls.y37 = pp3[7][1];
      // guiControls.y38 = pp3[8][1];
    }

    if (pp4.length > 0) {
      guiControls.x41 = pp4[0][0];
      guiControls.x42 = pp4[1][0];
      guiControls.x43 = pp4[2][0];
      guiControls.x44 = pp4[3][0];
      guiControls.x45 = pp4[4][0];
      guiControls.x46 = pp4[5][0];
      guiControls.x47 = pp4[6][0];
      guiControls.x48 = pp4[7][0];

      guiControls.y41 = pp4[0][1];
      guiControls.y42 = pp4[1][1];
      guiControls.y43 = pp4[2][1];
      guiControls.y44 = pp4[3][1];
      guiControls.y45 = pp4[4][1];
      guiControls.y46 = pp4[5][1];
      guiControls.y47 = pp4[6][1];
      guiControls.y48 = pp4[7][1];

      // Can delete if needed
      // guiControls.x41 = pp4[1][0];
      // guiControls.x42 = pp4[2][0];
      // guiControls.x43 = pp4[3][0];
      // guiControls.x44 = pp4[4][0];
      // guiControls.x45 = pp4[5][0];
      // guiControls.x46 = pp4[6][0];
      // guiControls.x47 = pp4[7][0];
      // guiControls.x48 = pp4[8][0];

      // guiControls.y41 = pp4[1][1];
      // guiControls.y42 = pp4[2][1];
      // guiControls.y43 = pp4[3][1];
      // guiControls.y44 = pp4[4][1];
      // guiControls.y45 = pp4[5][1];
      // guiControls.y46 = pp4[6][1];
      // guiControls.y47 = pp4[7][1];
      // guiControls.y48 = pp4[8][1];
    }

    if (pp5.length > 0) {
      guiControls.x51 = pp5[0][0];
      guiControls.x52 = pp5[1][0];
      guiControls.x53 = pp5[2][0];
      guiControls.x54 = pp5[3][0];
      guiControls.x55 = pp5[4][0];
      guiControls.x56 = pp5[5][0];
      guiControls.x57 = pp5[6][0];
      guiControls.x58 = pp5[7][0];

      guiControls.y51 = pp5[0][1];
      guiControls.y52 = pp5[1][1];
      guiControls.y53 = pp5[2][1];
      guiControls.y54 = pp5[3][1];
      guiControls.y55 = pp5[4][1];
      guiControls.y56 = pp5[5][1];
      guiControls.y57 = pp5[6][1];
      guiControls.y58 = pp5[7][1];

      // Can delete if needed
      // guiControls.x51 = pp5[1][0];
      // guiControls.x52 = pp5[2][0];
      // guiControls.x53 = pp5[3][0];
      // guiControls.x54 = pp5[4][0];
      // guiControls.x55 = pp5[5][0];
      // guiControls.x56 = pp5[6][0];
      // guiControls.x57 = pp5[7][0];
      // guiControls.x58 = pp5[8][0];

      // guiControls.y51 = pp5[1][1];
      // guiControls.y52 = pp5[2][1];
      // guiControls.y53 = pp5[3][1];
      // guiControls.y54 = pp5[4][1];
      // guiControls.y55 = pp5[5][1];
      // guiControls.y56 = pp5[6][1];
      // guiControls.y57 = pp5[7][1];
      // guiControls.y58 = pp5[8][1];
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
    console.log("Do check");
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
  }
  else if (guiControls.clusters == 2.0){
    console.log("Do check");
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
  }
  else if (guiControls.clusters == 3.0){
    console.log("Do check");
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
  }
  else if (guiControls.clusters == 4.0){
    console.log("Do check");
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
  }
  else if (guiControls.clusters == 5.0){
    console.log("Do check");
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
  }
}

// Implement rehgion growing algorithm on volume in here
function segmentRegions(clusterNo, sideNo) {
  console.log("Segment Regions");
  // console.log(npArray.data); // This is your volume data as a typed array
  // console.log(npArray.shape); // Shape of the numpy array

  // Find number of unique values in the volume
  const uniqueValues = new Set(npArray.data);
  // console.log(uniqueValues.size);

  // Find the minimum and maximum values in the volume
  // const min = npArray.data.reduce((acc, val) => Math.min(acc, val), Infinity);
  // const max = npArray.data.reduce((acc, val) => Math.max(acc, val), -Infinity);
  // console.log(min, max);

  const shape = window.npArray.shape;  // [d1, d2, d3, d4]
  const data = window.npArray.data;    // TypedArray with flattened data

  // Access element at indices [0, 0, 0, 0]
  const value1 = getElement(data, shape, [100, 100, 100, 0]);
  const value2 = getElement(data, shape, [100, 100, 100, 1]);
  const value3 = getElement(data, shape, [100, 100, 100, 2]);
  const value4 = getElement(data, shape, [100, 100, 100, 3]);
  // console.log(value1, value2, value3, value4);

  // Load boundary coordinates to array
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
  console.log(boundaryArray);
  
  // Inverse scaling of coordinates to get back GBC feature space coordinates
  var colorSpaceWidth = 400;//document.getElementById(this.iconColorSpaceContainerId).clientWidth;
  var colorSpaceHeight = 400;//this.colorSpaceWidth;
  var diameter = Math.round(colorSpaceHeight * 2.4 / 3.1);
  var xoffset = (colorSpaceWidth - diameter) / 2;
  var scaleGBC2Canvas = d3.scale.linear().domain([-1, 1]).range([xoffset, xoffset + diameter]);

  newBoundaryArray = [];
  for(i=0; i<clusterNo; i++){
    newBoundaryArray[i] = [];
    for(j=0; j<sideNo; j++){
      newBoundaryArray[i][j] = [];
      newBoundaryArray[i][j][0] = scaleGBC2Canvas.invert(boundaryArray[i][j][0]);
      newBoundaryArray[i][j][1] = scaleGBC2Canvas.invert(boundaryArray[i][j][1]);
    }
  }
  console.log(newBoundaryArray);


}