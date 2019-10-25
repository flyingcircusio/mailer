let
  # see https://nixos.org/channels/
  nixpkgs = fetchTarball https://releases.nixos.org/nixos/19.09/nixos-19.09beta284.49f57e66fe7/nixexprs.tar.xz;

in
{ pkgs ? import nixpkgs { } }:

with pkgs;
let

  shellInit = writeText "shellInit"''
    {{component.shellInit.replace('\n', '\n    ').strip()}}
  '';


in buildEnv {
    name = "mailer-1";
    paths = [
      (runCommand "profile" { } "install -D ${shellInit} $out/etc/profile.d/mailer.sh")
      python37
    ];
    extraOutputsToInstall = [ "out" "dev" "bin" "man" ];
}
