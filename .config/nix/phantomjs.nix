{ lib, stdenv, fetchurl, makeWrapper, coreutils, unzip }:

stdenv.mkDerivation rec {
  pname = "phantomjs";
  version = "2.1.1";
  src = fetchurl {
    url = "https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-macosx.zip";
    sha256 = "538cf488219ab27e309eafc629e2bcee9976990fe90b1ec334f541779150f8c1";
  };

  nativeBuildInputs = [ makeWrapper unzip ];

  installPhase = ''
    mkdir -p $out/bin
    cp bin/phantomjs $out/bin/
    wrapProgram $out/bin/phantomjs \
      --set PATH "${lib.makeBinPath [ coreutils ]}"
  '';

  meta = with lib; {
    description = "Headless WebKit scriptable with JavaScript";
    homepage = "http://phantomjs.org/";
    license = licenses.bsd3;
    platforms = platforms.darwin;
  };
}
