"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { BookPlus } from "lucide-react";
import { api } from "@/lib/api";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const bookSchema = z.object({
  title: z.string().min(2, "Title must be at least 2 characters").max(200),
  isbn: z.string().min(10, "ISBN must be at least 10 characters").max(32),
  author_name: z.string().min(2, "Author name must be at least 2 characters").max(120),
  total_copies: z.number().min(1, "Must have at least 1 copy").max(1000),
});

type BookFormValues = z.infer<typeof bookSchema>;

interface CreateBookDialogProps {
  onBookCreated: () => void;
}

export function CreateBookDialog({ onBookCreated }: CreateBookDialogProps) {
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<BookFormValues>({
    resolver: zodResolver(bookSchema),
    defaultValues: {
      title: "",
      isbn: "",
      author_name: "",
      total_copies: 1,
    },
  });

  const onSubmit = async (data: BookFormValues) => {
    setIsLoading(true);
    setError(null);
    try {
      await api.post("/api/v1/books", data);
      reset();
      setOpen(false);
      onBookCreated();
    } catch (err: any) {
      setError(
        err.response?.data?.detail || "Failed to register book. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        render={
          <Button>
            <BookPlus className="mr-2 h-4 w-4" />
            New Book
          </Button>
        }
      />
      <DialogContent className="sm:max-w-[560px]">
        <DialogHeader>
          <DialogTitle className="text-xl">Register New Book</DialogTitle>
          <DialogDescription>
            Add a new title to the library catalog. All fields are required.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 pt-2">
          {/* Title full width */}
          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              placeholder="e.g. The Lord of the Rings"
              {...register("title")}
              className={errors.title ? "border-destructive" : ""}
            />
            {errors.title && (
              <p className="text-sm text-destructive">{errors.title.message}</p>
            )}
          </div>

          {/* Author + Copies side by side */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="author_name">Author</Label>
              <Input
                id="author_name"
                placeholder="e.g. J.R.R. Tolkien"
                {...register("author_name")}
                className={errors.author_name ? "border-destructive" : ""}
              />
              {errors.author_name && (
                <p className="text-sm text-destructive">{errors.author_name.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="total_copies">Total Copies</Label>
              <Input
                id="total_copies"
                type="number"
                min="1"
                max="1000"
                {...register("total_copies", { valueAsNumber: true })}
                className={errors.total_copies ? "border-destructive" : ""}
              />
              {errors.total_copies && (
                <p className="text-sm text-destructive">{errors.total_copies.message}</p>
              )}
            </div>
          </div>

          {/* ISBN */}
          <div className="space-y-2">
            <Label htmlFor="isbn">ISBN</Label>
            <Input
              id="isbn"
              placeholder="e.g. 978-0544003415"
              {...register("isbn")}
              className={errors.isbn ? "border-destructive" : ""}
            />
            {errors.isbn && (
              <p className="text-sm text-destructive">{errors.isbn.message}</p>
            )}
          </div>

          {error && (
            <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
              <p className="text-sm text-destructive font-medium">{error}</p>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? "Saving..." : "Save Book"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
