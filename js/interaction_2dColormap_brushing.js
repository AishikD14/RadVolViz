// Maps geometric coordinate to color space
function CoordToColor(CX, CY) {
  [CX, CY] = ConstrainInUnit(CX, CY);
  return GBCtoHCL2(CX, CY);
}

function CoordToColor_ring(CX, CY) {
  [CX, CY] = ConstrainInUnit(CX, CY);
  return GBCtoHCL_ring(CX, CY);
}

function ConstrainInUnit(CX, CY) {
  let r = Math.sqrt(Math.pow(CX, 2) + Math.pow(CY, 2));
  if (r > 1) {
    CX /= r;
    CY /= r;
  }
  return [CX, CY];
}

function ObjtoArr(data) {
  var arr1 = new Array();
  data.map(function (d) {
    var arr = new Array();
    for (dd in d) {
      arr.push(d[dd]);
    }
    arr1.push(arr);
  });
  return arr1;
}

function ObjtoArrPC(d) {
  var arr1_pc = new Array();
  for (dd in d) {
    arr1_pc.push(d[dd]);
  }
  return arr1_pc;
}

// Loads CSV file during body load of HTML
function drawInitialchart(file) {
  //var fileName = "myDatawo0.csv";fullmyDatawo0 "halfmyDatawo0_CoAlTiDpc" "halfmy3Datawo0CoAlDpc""fullmy6Datawo0CoAlDpCMag.csv" fullmyDatawo0CeCoFeGd
  // d3.csv("new2_channel4.csv", function(d){
  // d3.csv("halfDataAlCoTiwo0.csv", function(d){ // Final for PAPER

  d3.csv("data10.csv", function (d) {
    dataS = d;
    // console.log(dataS);
    console.log("CSV data Iniital")
    console.log(dataS.length);
  });
}

// Copy the entire CSV data to a new array named data to be used in other places
function updateData() {
  num_points = guiControls.points;
  data = new Array();
  for (var i = 0; i < num_points; i++) {
    data.push(dataS[i]);//s = d[i];
  }
}

// Extract the header of the CSV file
function rowHeader(data) {
  var rowNum = 1;
  var rowName = [];
  data.map(function (row) {
    while (rowNum < 2) {
      rowName.push(Object.keys(row));
      rowNum++;
    }
  });
  return rowName;
}

// Not serving any purpose right now
function radioOnChange() {
  console.log("Interaction")
  helloWorld();
}

function newArray(A, B) {
  var C = [];
  var arrLen = A.length;
  for (var i = 0; i < arrLen; i++) {
    var obj = {};
    for (header in A[i]) {
      obj[header] = A[i][header];
    }
    obj.GBCX = B[i][0];
    obj.GBCY = B[i][1];
    C.push(obj);
  }
  return C;
}