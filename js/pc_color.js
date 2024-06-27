function rgba2rgb(RGBA, alphaPC) {
  var PCRGB = new Array(3);

  PCRGB[0] = (1.0 - alphaPC) * 0.0 + alphaPC * RGBA[0] / 255.0;
  PCRGB[1] = (1.0 - alphaPC) * 0.0 + alphaPC * RGBA[1] / 255.0;
  PCRGB[2] = (1.0 - alphaPC) * 0.0 + alphaPC * RGBA[2] / 255.0;

  return PCRGB;
}

function PC_Color(pc) {
  // console.log(dataPC);
  var ceRGBA = new Array(3);
  var coRGBA = new Array(3);
  var feRGBA = new Array(3);
  var gdRGBA = new Array(3);

  var ceRGB = new Array(3);
  var coRGB = new Array(3);
  var feRGB = new Array(3);
  var gdRGB = new Array(3);

  ceRGBA[0] = 0.0,
    ceRGBA[1] = 255.0,
    ceRGBA[2] = 255.0,

    coRGBA[0] = 127.5,
    coRGBA[1] = 255.0,
    coRGBA[2] = 0.0,

    feRGBA[0] = 255.0,
    feRGBA[1] = 0.0,
    feRGBA[2] = 0.0,

    gdRGBA[0] = 127.5,
    gdRGBA[1] = 0.0,
    gdRGBA[2] = 255.0;

  var ceA = pc[2];
  var coA = pc[3];
  var feA = pc[4];
  var gdA = pc[5];

  ceRGB = rgba2rgb(ceRGBA, ceA);
  coRGB = rgba2rgb(coRGBA, coA);
  feRGB = rgba2rgb(feRGBA, feA);
  gdRGB = rgba2rgb(gdRGBA, gdA);
  rr = (ceRGB[0] + coRGB[0] + feRGB[0] + gdRGB[0]);
  gg = (ceRGB[1] + coRGB[1] + feRGB[1] + gdRGB[1]);
  bb = (ceRGB[2] + coRGB[2] + feRGB[2] + gdRGB[2]);
  // console.log(rr*255,gg*255,bb*255);
  return d3.rgb(rr * 255, gg * 255, bb * 255).toString();
}
