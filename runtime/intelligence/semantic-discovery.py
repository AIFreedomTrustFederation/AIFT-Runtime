#!/usr/bin/env python3

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime


BASE = Path.home() / "AIFT"
REGISTRY = BASE / "registry"


IGNORE = {
    ".git",
    "node_modules",
    ".next",
    "dist",
    "build",
    "__pycache__"
}


def run(cmd, cwd=None):
    try:
        return subprocess.check_output(
            cmd,
            cwd=cwd,
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
    except:
        return ""


def detect_language(path):

    counts = {}

    extensions = {
        ".go":"Go",
        ".py":"Python",
        ".js":"JavaScript",
        ".ts":"TypeScript",
        ".tsx":"TypeScript React",
        ".jsx":"JavaScript React",
        ".rs":"Rust",
        ".java":"Java",
        ".cpp":"C++",
        ".c":"C",
        ".sh":"Shell",
        ".md":"Markdown"
    }

    for root, dirs, files in os.walk(path):

        dirs[:] = [
            d for d in dirs
            if d not in IGNORE
        ]

        for f in files:
            ext = Path(f).suffix

            if ext in extensions:
                lang = extensions[ext]
                counts[lang] = counts.get(lang,0)+1


    if not counts:
        return "Unknown"

    return max(
        counts,
        key=counts.get
    )


def detect_framework(path):

    checks = {
        "Next.js":"package.json",
        "Vite":"vite.config.js",
        "React":"package.json",
        "FastAPI":"requirements.txt",
        "Django":"manage.py",
        "Go Modules":"go.mod",
        "Rust Cargo":"Cargo.toml"
    }

    result=[]

    for name,file in checks.items():

        if (path/file).exists():
            result.append(name)

    return result


def detect_package_manager(path):

    files={
        "npm":"package.json",
        "pnpm":"pnpm-lock.yaml",
        "yarn":"yarn.lock",
        "pip":"requirements.txt",
        "go modules":"go.mod",
        "cargo":"Cargo.toml"
    }

    for manager,file in files.items():

        if (path/file).exists():
            return manager

    return "None"


def find_entrypoints(path):

    candidates=[]

    names={
        "main.go",
        "main.py",
        "index.js",
        "index.ts",
        "server.js",
        "app.py",
        "package.json",
        "docker-compose.yml"
    }

    for root,dirs,files in os.walk(path):

        dirs[:] = [
            d for d in dirs
            if d not in IGNORE
        ]

        for f in files:

            if f in names:

                candidates.append(
                    str(Path(root)/f)
                    .replace(str(path),"")
                )

    return candidates[:25]


def analyze_repo(path):

    repo={}

    repo["name"]=path.name
    repo["path"]=str(path)

    repo["language"]=detect_language(path)

    repo["frameworks"]=detect_framework(path)

    repo["package_manager"]=detect_package_manager(path)

    repo["entrypoints"]=find_entrypoints(path)


    repo["git_remote"]=run(
        [
            "git",
            "remote",
            "-v"
        ],
        cwd=path
    )


    repo["agents"]=[]

    for folder in [
        ".agents",
        "agents",
        "agent",
        "skills"
    ]:

        if (path/folder).exists():
            repo["agents"].append(folder)


    repo["manifests"]=[]

    for f in path.rglob("*manifest*.json"):

        if ".git" not in str(f):

            repo["manifests"].append(
                str(f.relative_to(path))
            )


    repo["analyzed_at"]=datetime.utcnow().isoformat()


    return repo



def discover():

    results=[]

    for item in BASE.iterdir():

        if not item.is_dir():
            continue

        if item.name in {
            "runtime",
            "registry"
        }:
            continue


        print(
            "[SCAN]",
            item.name
        )

        results.append(
            analyze_repo(item)
        )


    return results



if __name__=="__main__":

    data=discover()

    output=REGISTRY / "semantic-repo-brain.json"

    with open(output,"w") as f:

        json.dump(
            data,
            f,
            indent=2
        )


    print()
    print(
        "Semantic database created:"
    )

    print(output)

