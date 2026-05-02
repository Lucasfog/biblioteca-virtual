"use client";

import { useEffect, useState, useMemo } from "react";
import { api } from "@/lib/api";
import { Search, ShieldCheck } from "lucide-react";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { CreateBookDialog } from "@/components/books/CreateBookDialog";

interface Author {
  id: string;
  name: string;
}

interface Book {
  id: string;
  title: string;
  isbn: string;
  total_copies: number;
  available_copies: number;
  author: Author;
  created_at: string;
}

interface AvailabilityStatus {
  bookId: string;
  is_available: boolean;
  available_copies: number;
  loading: boolean;
}

export default function BooksPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [availability, setAvailability] = useState<Record<string, AvailabilityStatus>>({});

  const fetchBooks = async () => {
    setIsLoading(true);
    try {
      const response = await api.get("/api/v1/books/", {
        params: { limit: 100, offset: 0 },
      });
      setBooks(response.data.items || []);
    } catch (error) {
      console.error("Failed to fetch books", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchBooks();
  }, []);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    if (!q) return books;
    return books.filter(
      (b) =>
        b.title.toLowerCase().includes(q) ||
        b.author.name.toLowerCase().includes(q) ||
        b.isbn.toLowerCase().includes(q)
    );
  }, [books, search]);

  const handleCheckAvailability = async (bookId: string) => {
    setAvailability((prev) => ({
      ...prev,
      [bookId]: { bookId, is_available: false, available_copies: 0, loading: true },
    }));
    try {
      const response = await api.get(`/api/v1/books/${bookId}/availability`);
      const { available_copies, is_available } = response.data;
      setAvailability((prev) => ({
        ...prev,
        [bookId]: { bookId, is_available, available_copies, loading: false },
      }));
    } catch (error) {
      console.error("Failed to check availability", error);
      setAvailability((prev) => {
        const next = { ...prev };
        delete next[bookId];
        return next;
      });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Books Catalog</h2>
          <p className="text-muted-foreground mt-1">
            Manage the library inventory and verify book availability.
          </p>
        </div>
        <CreateBookDialog onBookCreated={fetchBooks} />
      </div>

      {/* Search Bar */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        <Input
          placeholder="Search by title, author, or ISBN..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="pl-6">Title</TableHead>
                <TableHead>Author</TableHead>
                <TableHead>ISBN</TableHead>
                <TableHead>Inventory</TableHead>
                <TableHead className="text-right pr-6">Availability</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                    Loading books...
                  </TableCell>
                </TableRow>
              ) : filtered.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                    {search ? `No books matching "${search}".` : "No books found."}
                  </TableCell>
                </TableRow>
              ) : (
                filtered.map((book) => {
                  const avail = availability[book.id];
                  return (
                    <TableRow key={book.id}>
                      <TableCell className="font-medium pl-6">{book.title}</TableCell>
                      <TableCell className="text-muted-foreground">{book.author.name}</TableCell>
                      <TableCell className="text-muted-foreground font-mono text-xs">{book.isbn}</TableCell>
                      <TableCell>
                        <Badge
                          className={
                            book.available_copies > 0
                              ? "bg-[#36F4A4]/15 text-[#36F4A4] border border-[#36F4A4]/30 hover:bg-[#36F4A4]/20"
                              : "bg-muted text-muted-foreground"
                          }
                        >
                          {book.available_copies} / {book.total_copies} Available
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right pr-6">
                        {avail && !avail.loading ? (
                          <Badge
                            className={
                              avail.is_available
                                ? "bg-[#36F4A4]/15 text-[#36F4A4] border border-[#36F4A4]/30"
                                : "bg-destructive/10 text-destructive border border-destructive/20"
                            }
                          >
                            <ShieldCheck className="h-3 w-3 mr-1" />
                            {avail.is_available
                              ? `${avail.available_copies} confirmed`
                              : "Unavailable"}
                          </Badge>
                        ) : (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleCheckAvailability(book.id)}
                            disabled={avail?.loading}
                          >
                            <ShieldCheck className="h-4 w-4 mr-1.5" />
                            {avail?.loading ? "Checking..." : "Verify"}
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
