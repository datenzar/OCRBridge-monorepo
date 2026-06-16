{ pkgs, lib, pythonEnvs }:

let
  commonTools = with pkgs; [
    pythonEnvs.python
    uv
    nodejs_24
    go
    ruff
    pyright
    tesseract
    poppler-utils
    file
    pythonEnvs.pdfocrPackage
    git
    curl
    nixpkgs-fmt
  ];

  dockerTools = lib.optionals pkgs.stdenv.hostPlatform.isLinux [
    pkgs.docker-client
    pkgs.docker-compose
  ];

  shellFor = { name, env, extraPackages ? [ ] }:
    pkgs.mkShell {
      inherit name;
      packages = commonTools ++ dockerTools ++ extraPackages ++ [ env ];
      env = {
        UV_NO_SYNC = "1";
        UV_PYTHON_DOWNLOADS = "never";
        UV_PYTHON = "${pythonEnvs.python}/bin/python";
      };
      shellHook = ''
        unset PYTHONPATH
        REPO_ROOT="${../.}"
        if git_root=$(git rev-parse --show-toplevel 2>/dev/null); then
          if [ -d "$git_root/apps/ocr-service" ]; then
            REPO_ROOT="$git_root"
          fi
        fi
        export REPO_ROOT

        OCRBRIDGE_STATE_ROOT="$REPO_ROOT"
        if [ ! -w "$OCRBRIDGE_STATE_ROOT" ]; then
          OCRBRIDGE_STATE_ROOT="$PWD/.ocrbridge-dev"
        fi
        mkdir -p "$OCRBRIDGE_STATE_ROOT/.cache/easyocr" "$OCRBRIDGE_STATE_ROOT/.tmp"
        export OCRBRIDGE_STATE_ROOT
        export EASYOCR_MODULE_PATH="$OCRBRIDGE_STATE_ROOT/.cache/easyocr"
        ${lib.optionalString pkgs.stdenv.hostPlatform.isDarwin ''
          export TMPDIR="$OCRBRIDGE_STATE_ROOT/.tmp"
        ''}

        export PATH="${env}/bin:$PATH"
        echo "OCRBridge Nix shell: ${name}"
      '';
    };
in
{
  default = shellFor {
    name = "ocrbridge-default";
    env = pythonEnvs.liteEnv;
  };

  lite = shellFor {
    name = "ocrbridge-lite";
    env = pythonEnvs.liteEnv;
  };
} // lib.optionalAttrs pythonEnvs.fullSupported {
  full = shellFor {
    name = "ocrbridge-full";
    env = pythonEnvs.fullEnv;
  };
} // lib.optionalAttrs pkgs.stdenv.hostPlatform.isDarwin {
  macos = shellFor {
    name = "ocrbridge-macos";
    env = pythonEnvs.macosEnv;
  };
}
