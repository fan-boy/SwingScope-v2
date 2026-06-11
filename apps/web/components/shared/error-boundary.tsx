"use client";
import { Component, type ReactNode } from "react";

export class ErrorBoundary extends Component<
  { children: ReactNode; fallback?: ReactNode },
  { hasError: boolean; message: string }
> {
  state = { hasError: false, message: "" };

  static getDerivedStateFromError(e: Error) {
    return { hasError: true, message: e.message };
  }

  componentDidCatch(e: Error, info: { componentStack: string }) {
    console.error("[ErrorBoundary]", e.message, info.componentStack);
  }

  render() {
    if (this.state.hasError)
      return (
        this.props.fallback ?? (
          <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-center space-y-2">
            <p className="text-sm font-medium text-destructive">Something went wrong</p>
            <p className="text-xs text-muted-foreground">{this.state.message}</p>
            <button
              onClick={() => this.setState({ hasError: false, message: "" })}
              className="text-xs text-primary hover:underline"
            >
              Try again
            </button>
          </div>
        )
      );
    return this.props.children;
  }
}
