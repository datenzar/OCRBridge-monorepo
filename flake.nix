{
  description = "OCRBridge monorepo";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    pyproject-nix.url = "github:pyproject-nix/pyproject.nix";
    uv2nix.url = "github:pyproject-nix/uv2nix";
    pyproject-build-systems.url = "github:pyproject-nix/build-system-pkgs";
    nix-darwin.url = "github:nix-darwin/nix-darwin";
    nix-darwin.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = inputs@{ self, nixpkgs, flake-utils, nix-darwin, ... }:
    flake-utils.lib.eachSystem (import ./nix/systems.nix)
      (system:
        let
          pkgs = import nixpkgs { inherit system; };
          isLinux = pkgs.stdenv.hostPlatform.isLinux;
          isDarwin = pkgs.stdenv.hostPlatform.isDarwin;
          pythonEnvs = import ./nix/python-envs.nix {
            inherit pkgs;
            inherit (pkgs) lib;
            inherit (inputs) pyproject-nix uv2nix pyproject-build-systems;
          };
          liteRuntimePath = pkgs.lib.makeBinPath [
            pythonEnvs.liteEnv
            pkgs.tesseract
            pkgs.poppler-utils
            pkgs.file
            pythonEnvs.pdfocrPackage
          ];
        in
        {
          packages = pythonEnvs.packages // {
            default = pythonEnvs.packages.ocr-service-lite;
          };

          apps = {
            default = flake-utils.lib.mkApp { drv = pythonEnvs.packages.ocr-service-lite; };
            ocr-service-lite = flake-utils.lib.mkApp { drv = pythonEnvs.packages.ocr-service-lite; };
          } // pkgs.lib.optionalAttrs pythonEnvs.fullSupported {
            ocr-service-full = flake-utils.lib.mkApp { drv = pythonEnvs.packages.ocr-service-full; };
          } // pkgs.lib.optionalAttrs isDarwin {
            ocr-service-macos = flake-utils.lib.mkApp { drv = pythonEnvs.packages.ocr-service-macos; };
          };

          devShells = import ./nix/dev-shells.nix {
            inherit pkgs;
            inherit (pkgs) lib;
            inherit pythonEnvs;
          };

          checks = {
            ocr-service-lite-import = pkgs.runCommand "ocr-service-lite-import" { } ''
              export PATH="${liteRuntimePath}:$PATH"
              export PYTHONPATH="${./apps/ocr-service}:''${PYTHONPATH:-}"
              ${pythonEnvs.liteEnv}/bin/python -c "import src.main; print('lite import ok')"
              mkdir -p $out
            '';

            ocr-service-lite-engines = pkgs.runCommand "ocr-service-lite-engines" { } ''
              export PATH="${liteRuntimePath}:$PATH"
              ${pythonEnvs.liteEnv}/bin/python - <<'PY'
              from importlib.metadata import entry_points

              names = {entry_point.name for entry_point in entry_points(group="ocrbridge.engines")}
              assert "tesseract" in names, sorted(names)
              print("lite engines ok")
              PY
              mkdir -p $out
            '';
          } // pkgs.lib.optionalAttrs isLinux {
            nixos-module-eval = import ./nix/tests/nixos-module-eval.nix {
              inherit nixpkgs self system;
            };
          } // pkgs.lib.optionalAttrs isDarwin {
            darwin-module-eval = import ./nix/tests/darwin-module-eval.nix {
              inherit nix-darwin nixpkgs self system;
            };
            ocr-service-macos-engines = pkgs.runCommand "ocr-service-macos-engines" { } ''
              ${pythonEnvs.macosEnv}/bin/python - <<'PY'
              from importlib.metadata import entry_points

              names = {entry_point.name for entry_point in entry_points(group="ocrbridge.engines")}
              assert "ocrmac" in names, sorted(names)
              print("macos engines ok")
              PY
              mkdir -p $out
            '';
          };
        }) // {
      nixosModules.ocr-service = import ./nix/modules/nixos/ocr-service.nix;
      darwinModules.ocr-service = import ./nix/modules/darwin/ocr-service.nix;
    };
}
