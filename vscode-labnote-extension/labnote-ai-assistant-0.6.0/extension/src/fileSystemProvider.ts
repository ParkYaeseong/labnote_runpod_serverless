// src/fileSystemProvider.ts

export interface FsDirent {
    name: string;
    isDirectory(): boolean;
}

export interface FileSystemProvider {
    exists(path: string): boolean;
    mkdir(path: string): void;
    readDir(path: string): FsDirent[];
    readTextFile(path: string): string;
    writeTextFile(path: string, content: string): void;
}