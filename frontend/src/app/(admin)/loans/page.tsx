"use client";

import { useEffect, useState, useMemo } from "react";
import { format, addDays } from "date-fns";
import { ArrowLeftRight, Search } from "lucide-react";
import { api } from "@/lib/api";

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
import { CreateLoanDialog } from "@/components/loans/CreateLoanDialog";

interface User {
  id: string;
  full_name: string;
}

interface Book {
  id: string;
  title: string;
  available_copies: number;
}

interface Loan {
  id: string;
  user_id: string;
  book_id: string;
  status: string;
  due_at: string;
}

type FilterTab = "active" | "overdue" | "user";

export default function LoansPage() {
  const [loans, setLoans] = useState<Loan[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [books, setBooks] = useState<Book[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<FilterTab>("active");
  const [userSearch, setUserSearch] = useState("");
  const [userIdQuery, setUserIdQuery] = useState("");

  const fetchLoans = async (tab: FilterTab, uid?: string) => {
    setIsLoading(true);
    try {
      let endpoint = "/api/v1/loans/active";
      if (tab === "overdue") endpoint = "/api/v1/loans/overdue";
      if (tab === "user" && uid) endpoint = `/api/v1/users/${uid}/loans`;

      const [loansRes, usersRes, booksRes] = await Promise.all([
        api.get(endpoint, { params: { limit: 100, offset: 0 } }),
        api.get("/api/v1/users/", { params: { limit: 100, offset: 0 } }),
        api.get("/api/v1/books/", { params: { limit: 100, offset: 0 } }),
      ]);
      setLoans(loansRes.data.items || []);
      setUsers(usersRes.data.items || []);
      setBooks(booksRes.data.items || []);
    } catch (error) {
      console.error("Failed to fetch loans data", error);
      setLoans([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLoans("active");
  }, []);

  const handleTabChange = (tab: FilterTab) => {
    setActiveTab(tab);
    if (tab !== "user") {
      fetchLoans(tab);
    }
  };

  const handleUserSearch = () => {
    const matched = users.find(
      (u) =>
        u.full_name.toLowerCase().includes(userSearch.toLowerCase()) ||
        u.id === userSearch
    );
    if (matched) {
      setUserIdQuery(matched.id);
      fetchLoans("user", matched.id);
    } else if (userSearch.length === 36) {
      // treat as raw UUID
      setUserIdQuery(userSearch);
      fetchLoans("user", userSearch);
    }
  };

  const getUserName = (id: string) => {
    const user = users.find((u) => u.id === id);
    return user ? user.full_name : "Unknown User";
  };

  const getBookTitle = (id: string) => {
    const book = books.find((b) => b.id === id);
    return book ? book.title : "Unknown Book";
  };

  const handleReturnLoan = async (loanId: string) => {
    try {
      const response = await api.post(`/api/v1/loans/${loanId}/return`);
      const returnedLoan = response.data;
      if (returnedLoan.fine_cents && returnedLoan.fine_cents > 0) {
        const fineBRL = (returnedLoan.fine_cents / 100).toFixed(2);
        alert(`Book returned successfully!\n\nWARNING: This book was returned late. A fine of R$ ${fineBRL} must be collected.`);
      } else {
        alert("Book returned successfully! No fine applied.");
      }
      fetchLoans(activeTab, userIdQuery || undefined);
    } catch (error) {
      console.error("Failed to return loan", error);
      alert("An error occurred while processing the return.");
    }
  };

  const tabConfig: { label: string; value: FilterTab }[] = [
    { label: "Active", value: "active" },
    { label: "Overdue", value: "overdue" },
    { label: "By User", value: "user" },
  ];

  const tabLabel = tabConfig.find((t) => t.value === activeTab)?.label ?? "Loans";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Loans</h2>
          <p className="text-muted-foreground mt-1">
            Monitor loans, process returns, and filter by status or user.
          </p>
        </div>
        <CreateLoanDialog users={users} books={books} onLoanCreated={() => fetchLoans(activeTab, userIdQuery || undefined)} />
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 border-b border-border pb-0">
        {tabConfig.map((tab) => (
          <button
            key={tab.value}
            onClick={() => handleTabChange(tab.value)}
            className={`px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${
              activeTab === tab.value
                ? "border-[#36F4A4] text-[#36F4A4]"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* User Search (shown only in "By User" tab) */}
      {activeTab === "user" && (
        <div className="flex gap-2 max-w-lg">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
            <Input
              placeholder="Search by user name or paste UUID..."
              value={userSearch}
              onChange={(e) => setUserSearch(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleUserSearch()}
              className="pl-9"
            />
          </div>
          <Button onClick={handleUserSearch} variant="outline" size="sm">
            Search
          </Button>
        </div>
      )}

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="pl-6">User</TableHead>
                <TableHead>Book</TableHead>
                <TableHead>Due Date</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right pr-6">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                    Loading loans...
                  </TableCell>
                </TableRow>
              ) : loans.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                    {activeTab === "user" && !userIdQuery
                      ? "Search for a user above to see their loans."
                      : `No ${tabLabel.toLowerCase()} loans found.`}
                  </TableCell>
                </TableRow>
              ) : (
                loans.map((loan) => {
                  const isOverdue = activeTab === "overdue" || new Date(loan.due_at) < new Date();
                  return (
                    <TableRow key={loan.id}>
                      <TableCell className="font-medium pl-6">{getUserName(loan.user_id)}</TableCell>
                      <TableCell className="text-muted-foreground">{getBookTitle(loan.book_id)}</TableCell>
                      <TableCell className={isOverdue ? "text-destructive font-medium" : "text-muted-foreground"}>
                        {format(new Date(loan.due_at), "MMM d, yyyy")}
                      </TableCell>
                      <TableCell>
                        {isOverdue ? (
                          <Badge className="bg-destructive/10 text-destructive border border-destructive/20 hover:bg-destructive/20">
                            Overdue
                          </Badge>
                        ) : (
                          <Badge className="bg-[#36F4A4]/15 text-[#36F4A4] border border-[#36F4A4]/30 hover:bg-[#36F4A4]/20">
                            Active
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right pr-6">
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleReturnLoan(loan.id)}
                        >
                          <ArrowLeftRight className="h-4 w-4 mr-2" />
                          Process Return
                        </Button>
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
