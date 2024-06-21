//
//
// if ( ! Detector.webgl ) Detector.addGetWebGLMessage();
//
// var container, stats;
// var camera, sceneFirstPass, sceneSecondPass, renderer;
// var canvas;
// var clock = new THREE.Clock();
// var rtTexture, transferTexture;
// var cubeTextures = ['Default'];
// var histogram = [];
// var guiControls;
//
// var materialSecondPass;
// init();
// animate();
// // helloWorld();
//
// // downloadButton.addEventListener("click", function(e){
// // 		canvas.toBlob(
// // 			function(blob){
// // 				var a = document.createElement("a");
// // 				a.download = "volume.png";
// // 				a.href = URL.createObjectURL(blob);
// // 				a.dispatchEvent(new MouseEvent(`click`, {bubbles: true, cancelable: true, view: window}));
// // 			},
// // 			"image/png"
// // 		);
// // 	});
//
// function onWindowResize( event ) {
//
//   camera.aspect = window.innerWidth / window.innerHeight;
//   camera.updateProjectionMatrix();
//   renderer.setSize( window.innerWidth, window.innerHeight );
// }
//
// var newObj;
// function animate() {
//
//   requestAnimationFrame( animate );
//
//   updateData();
//   render();
//   stats.update();
//
//
//   if (newObj == undefined){
//     newObj = {}
//   }
//   if (JSON.stringify(guiControls) === JSON.stringify(newObj)){
//     // console.log("Now Equal");
//   }
//   else {
//     // console.log("Not equal so came here");
//     Object.assign(newObj, guiControls)
//     helloWorld();
//   }
//
//
//
// }
//
// function render() {
//
//
//
//
// //	helloWorld();
//   var delta = clock.getDelta();
//   //Render first pass and store the world space coords of the back face fragments into the texture.
//   renderer.render( sceneFirstPass, camera, rtTexture, true );
//
//   // console.log(gl_Position);
//   //Render the second pass and perform the volume rendering.
//   renderer.render( sceneSecondPass, camera );
//   materialSecondPass.uniforms.steps.value = guiControls.steps;
//   materialSecondPass.uniforms.alphaCorrection.value = guiControls.alphaCorrection;
//
//   materialSecondPass.uniforms.modeGBC.value = guiControls.modeGBC;
//   materialSecondPass.uniforms.rotateVar3D.value = guiControls.rotateVar3D;
//
// //  materialSecondPass.uniforms.colorSpaceWidth1.value = guiControls.colorSpaceWidth1;
//   materialSecondPass.uniforms.radialValue.value = guiControls.radialValue;
//   materialSecondPass.uniforms.lensMode.value = guiControls.lensMode;
//   materialSecondPass.uniforms.lensAng.value = guiControls.lensAng;
//   materialSecondPass.uniforms.lensMove.value = guiControls.lensMove;
//
//   materialSecondPass.uniforms.binValue.value = guiControls.binValue;
//   materialSecondPass.uniforms.testValue.value = guiControls.testValue;
//   materialSecondPass.uniforms.xValue.value = guiControls.xValue;
//   materialSecondPass.uniforms.yValue.value = guiControls.yValue;
//   materialSecondPass.uniforms.radiusR.value = guiControls.radiusR;
//   materialSecondPass.uniforms.arcWidth.value = guiControls.arcWidth;
//   materialSecondPass.uniforms.modeARC.value = guiControls.modeARC;
//   materialSecondPass.uniforms.startAng.value = guiControls.startAng;
//   materialSecondPass.uniforms.points.value = guiControls.points;
//   materialSecondPass.uniforms.rangeVal.value = guiControls.rangeVal;
//   materialSecondPass.uniforms.maxrangeVal.value = guiControls.maxrangeVal;
//
//   materialSecondPass.uniforms.xClippingPlaneMin.value = guiControls.xClippingPlaneMin;
//   materialSecondPass.uniforms.xClippingPlaneMin2.value = guiControls.xClippingPlaneMin2;
//   materialSecondPass.uniforms.xClippingPlaneMax.value = guiControls.xClippingPlaneMax;
//   materialSecondPass.uniforms.yClippingPlaneMin.value = guiControls.yClippingPlaneMin;
//   materialSecondPass.uniforms.yClippingPlaneMax.value = guiControls.yClippingPlaneMax;
//   materialSecondPass.uniforms.zClippingPlaneMin.value = guiControls.zClippingPlaneMin;
//   materialSecondPass.uniforms.zClippingPlaneMax.value = guiControls.zClippingPlaneMax;
//   materialSecondPass.uniforms.wClippingPlane.value = guiControls.wClippingPlane;
//   materialSecondPass.uniforms.axisClipping.value = guiControls.axisClipping;
//   materialSecondPass.uniforms.x1.value = guiControls.x1;
//   materialSecondPass.uniforms.x2.value = guiControls.x2;
//   materialSecondPass.uniforms.x3.value = guiControls.x3;
//   materialSecondPass.uniforms.x4.value = guiControls.x4;
//   materialSecondPass.uniforms.x5.value = guiControls.x5;
//   materialSecondPass.uniforms.x6.value = guiControls.x6;
//   materialSecondPass.uniforms.x7.value = guiControls.x7;
//   materialSecondPass.uniforms.x8.value = guiControls.x8;
//   materialSecondPass.uniforms.y1.value = guiControls.y1;
//   materialSecondPass.uniforms.y2.value = guiControls.y2;
//   materialSecondPass.uniforms.y3.value = guiControls.y3;
//   materialSecondPass.uniforms.y4.value = guiControls.y4;
//   materialSecondPass.uniforms.y5.value = guiControls.y5;
//   materialSecondPass.uniforms.y6.value = guiControls.y6;
//   materialSecondPass.uniforms.y7.value = guiControls.y7;
//   materialSecondPass.uniforms.y8.value = guiControls.y8;
//   materialSecondPass.uniforms.x11.value = guiControls.x11;
//   materialSecondPass.uniforms.x12.value = guiControls.x12;
//   materialSecondPass.uniforms.x13.value = guiControls.x13;
//   materialSecondPass.uniforms.x14.value = guiControls.x14;
//   materialSecondPass.uniforms.x15.value = guiControls.x15;
//   materialSecondPass.uniforms.x16.value = guiControls.x16;
//   materialSecondPass.uniforms.x17.value = guiControls.x17;
//   materialSecondPass.uniforms.x18.value = guiControls.x18;
//   materialSecondPass.uniforms.y11.value = guiControls.y11;
//   materialSecondPass.uniforms.y12.value = guiControls.y12;
//   materialSecondPass.uniforms.y13.value = guiControls.y13;
//   materialSecondPass.uniforms.y14.value = guiControls.y14;
//   materialSecondPass.uniforms.y15.value = guiControls.y15;
//   materialSecondPass.uniforms.y16.value = guiControls.y16;
//   materialSecondPass.uniforms.y17.value = guiControls.y17;
//   materialSecondPass.uniforms.y18.value = guiControls.y18;
//
//   materialSecondPass.uniforms.x31.value = guiControls.x31;
//   materialSecondPass.uniforms.x32.value = guiControls.x32;
//   materialSecondPass.uniforms.x33.value = guiControls.x33;
//   materialSecondPass.uniforms.x34.value = guiControls.x34;
//   materialSecondPass.uniforms.x35.value = guiControls.x35;
//   materialSecondPass.uniforms.x36.value = guiControls.x36;
//   materialSecondPass.uniforms.x37.value = guiControls.x37;
//   materialSecondPass.uniforms.x38.value = guiControls.x38;
//   materialSecondPass.uniforms.y31.value = guiControls.y31;
//   materialSecondPass.uniforms.y32.value = guiControls.y32;
//   materialSecondPass.uniforms.y33.value = guiControls.y33;
//   materialSecondPass.uniforms.y34.value = guiControls.y34;
//   materialSecondPass.uniforms.y35.value = guiControls.y35;
//   materialSecondPass.uniforms.y36.value = guiControls.y36;
//   materialSecondPass.uniforms.y37.value = guiControls.y37;
//   materialSecondPass.uniforms.y38.value = guiControls.y38;
//
//   materialSecondPass.uniforms.x41.value = guiControls.x41;
//   materialSecondPass.uniforms.x42.value = guiControls.x42;
//   materialSecondPass.uniforms.x43.value = guiControls.x43;
//   materialSecondPass.uniforms.x44.value = guiControls.x44;
//   materialSecondPass.uniforms.x45.value = guiControls.x45;
//   materialSecondPass.uniforms.x46.value = guiControls.x46;
//   materialSecondPass.uniforms.x47.value = guiControls.x47;
//   materialSecondPass.uniforms.x48.value = guiControls.x48;
//   materialSecondPass.uniforms.y41.value = guiControls.y41;
//   materialSecondPass.uniforms.y42.value = guiControls.y42;
//   materialSecondPass.uniforms.y43.value = guiControls.y43;
//   materialSecondPass.uniforms.y44.value = guiControls.y44;
//   materialSecondPass.uniforms.y45.value = guiControls.y45;
//   materialSecondPass.uniforms.y46.value = guiControls.y46;
//   materialSecondPass.uniforms.y47.value = guiControls.y47;
//   materialSecondPass.uniforms.y48.value = guiControls.y48;
//
//   materialSecondPass.uniforms.x51.value = guiControls.x51;
//   materialSecondPass.uniforms.x52.value = guiControls.x52;
//   materialSecondPass.uniforms.x53.value = guiControls.x53;
//   materialSecondPass.uniforms.x54.value = guiControls.x54;
//   materialSecondPass.uniforms.x55.value = guiControls.x55;
//   materialSecondPass.uniforms.x56.value = guiControls.x56;
//   materialSecondPass.uniforms.x57.value = guiControls.x57;
//   materialSecondPass.uniforms.x58.value = guiControls.x58;
//   materialSecondPass.uniforms.y51.value = guiControls.y51;
//   materialSecondPass.uniforms.y52.value = guiControls.y52;
//   materialSecondPass.uniforms.y53.value = guiControls.y53;
//   materialSecondPass.uniforms.y54.value = guiControls.y54;
//   materialSecondPass.uniforms.y55.value = guiControls.y55;
//   materialSecondPass.uniforms.y56.value = guiControls.y56;
//   materialSecondPass.uniforms.y57.value = guiControls.y57;
//   materialSecondPass.uniforms.y58.value = guiControls.y58;
//   materialSecondPass.uniforms.hslh1.value = guiControls.hslh1;
//   materialSecondPass.uniforms.hslh2.value = guiControls.hslh2;
//   materialSecondPass.uniforms.hslh3.value = guiControls.hslh3;
//   materialSecondPass.uniforms.hslh4.value = guiControls.hslh4;
//   materialSecondPass.uniforms.hslh5.value = guiControls.hslh5;
//   materialSecondPass.uniforms.hsls1.value = guiControls.hsls1;
//   materialSecondPass.uniforms.hsls2.value = guiControls.hsls2;
//   materialSecondPass.uniforms.hsls3.value = guiControls.hsls3;
//   materialSecondPass.uniforms.hsls4.value = guiControls.hsls4;
//   materialSecondPass.uniforms.hsls5.value = guiControls.hsls5;
//   materialSecondPass.uniforms.hsll.value = guiControls.hsll;
//   materialSecondPass.uniforms.polySide.value = guiControls.polySide;
//   materialSecondPass.uniforms.clusters.value = guiControls.clusters;
//   materialSecondPass.uniforms.brushMode.value = guiControls.brushMode;
//   materialSecondPass.uniforms.stDev.value = guiControls.stDev;
//   //materialSecondPass.uniforms["defaultLens"] = guiControls.defaultLens;
//   // materialSecondPass.uniforms.passingA.value = guiControls.passA;
//   // materialSecondPass.uniforms.passingB.value = guiControls.passB;
//   // materialSecondPass.uniforms.passingC.value = guiControls.passC;
//   // materialSecondPass.uniforms.passingD.value = guiControls.passD;
//
// }
