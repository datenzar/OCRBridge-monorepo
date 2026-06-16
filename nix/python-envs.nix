{ pkgs
, lib
, pyproject-nix
, uv2nix
, pyproject-build-systems
}:

let
  python = if pkgs ? python314 then pkgs.python314 else pkgs.python313;
  fullSupported = pkgs.stdenv.hostPlatform.system != "x86_64-darwin";

  workspace = uv2nix.lib.workspace.loadWorkspace {
    workspaceRoot = ../.;
  };

  pyprojectOverlay = workspace.mkPyprojectOverlay {
    sourcePreference = "wheel";
  };

  pythonBase = pkgs.callPackage pyproject-nix.build.packages {
    inherit python;
  };

  packageOverrides = _final: prev: {
    python-magic = prev.python-magic.overrideAttrs (old: {
      propagatedBuildInputs = (old.propagatedBuildInputs or [ ]) ++ [ pkgs.file ];
    });
  };

  pythonSet = pythonBase.overrideScope (
    lib.composeManyExtensions [
      pyproject-build-systems.overlays.wheel
      pyprojectOverlay
      packageOverrides
    ]
  );

  envFor = name: deps: pythonSet.mkVirtualEnv name deps;

  liteEnv = envFor "ocr-service-lite-env" {
    ocr-service = [ "tesseract" ];
  };

  fullEnv = envFor "ocr-service-full-env" {
    ocr-service = [ "tesseract" "easyocr" ];
  };

  macosEnv = envFor "ocr-service-macos-env" {
    ocr-service = [ "tesseract" "ocrmac" ];
  };

  commonRuntimePackages = [
    pkgs.poppler-utils
    pkgs.tesseract
    pkgs.file
    pdfocrPackage
  ];

  pdfocrPackage = pkgs.buildGoModule rec {
    pname = "pdfocr";
    version = "0-unstable-2026-01-20";
    src = pkgs.fetchFromGitHub {
      owner = "gardar";
      repo = "ocrchestra";
      rev = "aaae7e4d40e97931d4e06c0aa2e3ed77e3eb89d8";
      hash = "sha256-AQ3yB5rwj7DPQEmCLuwDwLo0oWNNy2mz3AoQqueta9c=";
    };
    vendorHash = "sha256-HBejxfSdSDIl6rq4D4h7l9OSG2yfuM38SwxrBTeK9xw=";
    subPackages = [ "cmd/pdfocr" ];
  };

  makeService = { name, env, extraRuntimePackages ? [ ] }:
    pkgs.writeShellApplication {
      inherit name;
      runtimeInputs = commonRuntimePackages ++ extraRuntimePackages;
      text = ''
        export PATH="${env}/bin:$PATH"
        export API_HOST="''${API_HOST:-0.0.0.0}"
        export API_PORT="''${API_PORT:-8000}"
        export API_WORKERS="''${API_WORKERS:-4}"
        exec ${env}/bin/uvicorn src.main:app \
          --app-dir ${../apps/ocr-service} \
          --host "$API_HOST" \
          --port "$API_PORT" \
          --workers "$API_WORKERS" \
          "$@"
      '';
      meta.mainProgram = name;
    };
in
{
  inherit python pythonSet liteEnv fullEnv macosEnv pdfocrPackage fullSupported;

  packages = {
    ocr-service-lite = makeService {
      name = "ocr-service-lite";
      env = liteEnv;
    };
  } // lib.optionalAttrs fullSupported {
    ocr-service-full = makeService {
      name = "ocr-service-full";
      env = fullEnv;
    };
  } // lib.optionalAttrs pkgs.stdenv.hostPlatform.isDarwin {
    ocr-service-macos = makeService {
      name = "ocr-service-macos";
      env = macosEnv;
    };
  };
}
