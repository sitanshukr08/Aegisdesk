import { cn } from "@/lib/utils";

interface Props {
  children: React.ReactNode;
  className?: string;
  as?: "h1" | "h2" | "h3" | "span" | "div" | "p";
}

export function DotMatrixText({ children, className, as: Tag = "span" }: Props) {
  return <Tag className={cn("font-mono-dot", className)}>{children}</Tag>;
}