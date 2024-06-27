
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
  // console.log(data);
  var arr1_pc = new Array();
  // data.map(function(d){
  // var arr_pc = new Array();
  for (dd in d) {
    arr1_pc.push(d[dd]);
  }

  // arr1_pc.push(arr_pc);
  // });

  return arr1_pc;
}

function drawInitialchart(file) {
  //var fileName = "myDatawo0.csv";fullmyDatawo0 "halfmyDatawo0_CoAlTiDpc" "halfmy3Datawo0CoAlDpc""fullmy6Datawo0CoAlDpCMag.csv" fullmyDatawo0CeCoFeGd
  // d3.csv("new2_channel4.csv", function(d){
  // d3.csv("halfDataAlCoTiwo0.csv", function(d){ // Final for PAPER

  d3.csv("data10.csv", function (d) {
    dataS = d;
    // console.log(dataS);

  });

}

function updateData() {
  num_points = guiControls.points;
  data = new Array();
  for (var i = 0; i < num_points; i++) {
    data.push(dataS[i]);//s = d[i];

  }
}

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

function radioOnChange() {
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
//
// From Will Harrison to Everyone:  04:58 PM
// I’m just turning off my camera while I eat my breakfast :D
// From Will Harrison to Everyone:  05:07 PM
// Australian trivia: we call it “Where’s Wally”!
// From Alexandre Reynaud to Everyone:  05:07 PM
// He is called Charlie in France
// From Will Harrison to Everyone:  05:09 PM
// Ha!
// From Jan Skerswetat to Everyone:  05:09 PM
// Walter in German
// From Peter Bex to Everyone:  05:10 PM
// In the UK it's called "Nobody gives a shit"
// From Will Harrison to Everyone:  05:11 PM
// 😅
