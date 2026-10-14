import { useMemo, useState } from 'react'
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from '@tanstack/react-table'
import { ArrowDownUp, ChevronLeft, ChevronRight, Search } from 'lucide-react'
import { type Anomaly, date, score } from '@/lib/api'
import { Button } from './ui/button'

export function SignalTable({
  rows,
  onSelect,
}: {
  rows: Anomaly[]
  onSelect: (symbol: string) => void
}) {
  const [sorting, setSorting] = useState<SortingState>([{ id: 'date', desc: true }])
  const [filter, setFilter] = useState('')
  const data = useMemo(
    () =>
      rows.filter((r) =>
        `${r.symbol} ${r.name} ${r.signal}`.toLowerCase().includes(filter.toLowerCase()),
      ),
    [rows, filter],
  )
  const columns = useMemo<ColumnDef<Anomaly>[]>(
    () => [
      {
        accessorKey: 'symbol',
        header: 'Instrument',
        cell: ({ row }) => (
          <button className="instrument-link" onClick={() => onSelect(row.original.symbol)}>
            <span className="ticker-icon">{row.original.symbol.slice(0, 2)}</span>
            <span>
              <strong>{row.original.symbol}</strong>
              <small>{row.original.name}</small>
            </span>
          </button>
        ),
      },
      {
        accessorKey: 'date',
        header: 'Observed',
        cell: ({ getValue }) => <span className="mono table-date">{date(getValue<string>())}</span>,
      },
      {
        accessorKey: 'signal',
        header: 'Signal',
        cell: ({ getValue }) => <span className="signal-type">{getValue<string>()}</span>,
      },
      {
        accessorKey: 'max_zscore',
        header: '|z| max',
        cell: ({ getValue }) => (
          <span className={`mono z-score ${(getValue<number | null>() ?? 0) >= 4 ? 'high' : ''}`}>
            {score(getValue<number | null>())}
          </span>
        ),
      },
    ],
    [onSelect],
  )
  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 6 } },
  })
  return (
    <>
      <div className="table-filter">
        <Search size={13} />
        <input
          aria-label="Filter historical anomalies"
          placeholder="Filter instrument or signal…"
          value={filter}
          onChange={(event) => {
            setFilter(event.target.value)
            table.setPageIndex(0)
          }}
        />
        <span className="mono">{data.length} records</span>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            {table.getHeaderGroups().map((group) => (
              <tr key={group.id}>
                {group.headers.map((header) => (
                  <th
                    key={header.id}
                    aria-sort={
                      header.column.getIsSorted() === 'asc'
                        ? 'ascending'
                        : header.column.getIsSorted() === 'desc'
                          ? 'descending'
                          : 'none'
                    }
                  >
                    <button onClick={header.column.getToggleSortingHandler()}>
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      <ArrowDownUp size={10} />
                    </button>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {!data.length && <div className="empty">No historical signals match this filter.</div>}
      </div>
      <div className="table-footer">
        <span>Statistical flags · human review required</span>
        <div>
          <span className="mono">
            {data.length ? table.getState().pagination.pageIndex + 1 : 0} / {table.getPageCount()}
          </span>
          <Button
            variant="ghost"
            size="icon"
            disabled={!table.getCanPreviousPage()}
            onClick={() => table.previousPage()}
            aria-label="Previous anomaly page"
          >
            <ChevronLeft size={14} />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            disabled={!table.getCanNextPage()}
            onClick={() => table.nextPage()}
            aria-label="Next anomaly page"
          >
            <ChevronRight size={14} />
          </Button>
        </div>
      </div>
    </>
  )
}
