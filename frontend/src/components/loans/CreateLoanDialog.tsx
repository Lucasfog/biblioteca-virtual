"use client";

import { useMemo, useState } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { BookUp, Calendar, Users, BookOpen } from "lucide-react";
import { addDays, format } from "date-fns";
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
import { Label } from "@/components/ui/label";

const loanSchema = z.object({
  user_id: z.string().min(1, "Please select a user"),
  book_id: z.string().min(1, "Please select a book"),
});

type LoanFormValues = z.infer<typeof loanSchema>;

interface UserSnippet {
  id: string;
  full_name: string;
}

interface BookSnippet {
  id: string;
  title: string;
  available_copies: number;
}

interface CreateLoanDialogProps {
  users: UserSnippet[];
  books: BookSnippet[];
  onLoanCreated: () => void;
}

export function CreateLoanDialog({ users, books, onLoanCreated }: CreateLoanDialogProps) {
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState("");
  const [selectedBookId, setSelectedBookId] = useState("");

  const {
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<LoanFormValues>({
    resolver: zodResolver(loanSchema),
    defaultValues: { user_id: "", book_id: "" },
  });

  const availableBooks = useMemo(() => books.filter((b) => b.available_copies > 0), [books]);
  const dueDate = addDays(new Date(), 14);

  const selectedUserName = users.find((u) => u.id === selectedUserId)?.full_name;
  const selectedBookTitle = books.find((b) => b.id === selectedBookId)?.title;

  const onSubmit = async (data: LoanFormValues) => {
    setIsLoading(true);
    setError(null);
    try {
      await api.post("/api/v1/loans", data);
      reset();
      setSelectedUserId("");
      setSelectedBookId("");
      setOpen(false);
      onLoanCreated();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create loan. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    reset();
    setSelectedUserId("");
    setSelectedBookId("");
    setError(null);
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) handleClose(); else setOpen(true); }}>
      <DialogTrigger
        render={
          <Button>
            <BookUp className="mr-2 h-4 w-4" />
            New Loan
          </Button>
        }
      />
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle className="text-xl">Register New Loan</DialogTitle>
          <DialogDescription>
            Select a user and an available book to create a loan.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 pt-2">

          {/* User — native combobox using a styled select */}
          <div className="space-y-2">
            <Label className="flex items-center gap-1.5">
              <Users className="h-3.5 w-3.5 text-muted-foreground" />
              User
            </Label>
            <Controller
              name="user_id"
              control={control}
              render={({ field }) => (
                <div className="relative">
                  <select
                    value={field.value}
                    onChange={(e) => {
                      field.onChange(e.target.value);
                      setSelectedUserId(e.target.value);
                    }}
                    className={`w-full h-10 rounded-lg border ${errors.user_id ? "border-destructive" : "border-input"} bg-background px-3 text-sm text-foreground outline-none focus:ring-2 focus:ring-[#36F4A4] appearance-none pr-8 cursor-pointer`}
                  >
                    <option value="" disabled>Select a user...</option>
                    {users.map((u) => (
                      <option key={u.id} value={u.id}>{u.full_name}</option>
                    ))}
                  </select>
                  <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                      <path d="M2 4l4 4 4-4" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                </div>
              )}
            />
            {selectedUserName && (
              <p className="text-xs text-[#36F4A4] flex items-center gap-1">
                <Users className="h-3 w-3" /> {selectedUserName} selected
              </p>
            )}
            {errors.user_id && <p className="text-sm text-destructive">{errors.user_id.message}</p>}
          </div>

          {/* Book — native select */}
          <div className="space-y-2">
            <Label className="flex items-center gap-1.5">
              <BookOpen className="h-3.5 w-3.5 text-muted-foreground" />
              Book
            </Label>
            <Controller
              name="book_id"
              control={control}
              render={({ field }) => (
                <div className="relative">
                  <select
                    value={field.value}
                    onChange={(e) => {
                      field.onChange(e.target.value);
                      setSelectedBookId(e.target.value);
                    }}
                    disabled={availableBooks.length === 0}
                    className={`w-full h-10 rounded-lg border ${errors.book_id ? "border-destructive" : "border-input"} bg-background px-3 text-sm text-foreground outline-none focus:ring-2 focus:ring-[#36F4A4] appearance-none pr-8 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed`}
                  >
                    <option value="" disabled>
                      {availableBooks.length === 0 ? "No books available" : "Select a book..."}
                    </option>
                    {availableBooks.map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.title} ({b.available_copies} available)
                      </option>
                    ))}
                  </select>
                  <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                      <path d="M2 4l4 4 4-4" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                </div>
              )}
            />
            {selectedBookTitle && (
              <p className="text-xs text-[#36F4A4] flex items-center gap-1">
                <BookOpen className="h-3 w-3" /> {selectedBookTitle} selected
              </p>
            )}
            {errors.book_id && <p className="text-sm text-destructive">{errors.book_id.message}</p>}
          </div>

          {/* Due Date Preview */}
          <div className="flex items-center gap-3 p-3 rounded-lg border border-border bg-muted/40 text-sm">
            <Calendar className="h-4 w-4 text-[#36F4A4] shrink-0" />
            <div>
              <span className="text-muted-foreground">Estimated due date: </span>
              <span className="font-medium text-foreground">{format(dueDate, "MMMM d, yyyy")}</span>
              <span className="text-muted-foreground ml-1">(14 days from today)</span>
            </div>
          </div>

          {error && (
            <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
              <p className="text-sm text-destructive font-medium">{error}</p>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading || availableBooks.length === 0}>
              {isLoading ? "Saving..." : "Confirm Loan"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
