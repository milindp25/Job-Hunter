'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { Search, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import type { JobSearchParams } from '@/lib/types';

interface JobFiltersProps {
  filters: JobSearchParams;
  onFilterChange: (filters: JobSearchParams) => void;
}

const JOB_TYPES = [
  { value: '', label: 'All Types' },
  { value: 'full_time', label: 'Full-time' },
  { value: 'part_time', label: 'Part-time' },
  { value: 'contract', label: 'Contract' },
  { value: 'internship', label: 'Internship' },
];

const SOURCES = [
  { value: '', label: 'All Sources' },
  { value: 'remoteok', label: 'RemoteOK' },
  { value: 'themuse', label: 'The Muse' },
  { value: 'adzuna', label: 'Adzuna' },
  { value: 'usajobs', label: 'USAJobs' },
];

export function JobFilters({ filters, onFilterChange }: JobFiltersProps) {
  const [query, setQuery] = useState(filters.query ?? '');
  const [location, setLocation] = useState(filters.location ?? '');
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(null);

  const debouncedUpdate = useCallback(
    (field: keyof JobSearchParams, value: string) => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        onFilterChange({ ...filters, [field]: value || undefined, page: 1 });
      }, 400);
    },
    [filters, onFilterChange],
  );

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  function handleQueryChange(value: string) {
    setQuery(value);
    debouncedUpdate('query', value);
  }

  function handleLocationChange(value: string) {
    setLocation(value);
    debouncedUpdate('location', value);
  }

  function handleSelectChange(field: keyof JobSearchParams, value: string) {
    onFilterChange({ ...filters, [field]: value || undefined, page: 1 });
  }

  function handleRemoteToggle() {
    const nextRemote = filters.is_remote ? undefined : true;
    onFilterChange({ ...filters, is_remote: nextRemote, page: 1 });
  }

  function handleSalaryChange(field: 'salary_min' | 'salary_max', value: string) {
    const num = value ? parseInt(value, 10) : undefined;
    onFilterChange({ ...filters, [field]: num, page: 1 });
  }

  function clearFilters() {
    setQuery('');
    setLocation('');
    onFilterChange({ page: 1 });
  }

  const hasFilters = !!(
    filters.query ||
    filters.location ||
    filters.job_type ||
    filters.source ||
    filters.is_remote ||
    filters.salary_min ||
    filters.salary_max
  );

  return (
    <div className="space-y-4">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/40" />
        <Input
          placeholder="Search jobs..."
          value={query}
          onChange={(e) => handleQueryChange(e.target.value)}
          className="pl-9"
          aria-label="Search jobs"
        />
      </div>

      <div>
        <label htmlFor="location-filter" className="mb-1.5 block text-xs font-medium text-foreground/70">
          Location
        </label>
        <Input
          id="location-filter"
          placeholder="City, state, or country"
          value={location}
          onChange={(e) => handleLocationChange(e.target.value)}
        />
      </div>

      <div>
        <label htmlFor="job-type-filter" className="mb-1.5 block text-xs font-medium text-foreground/70">
          Job Type
        </label>
        <Select
          id="job-type-filter"
          value={filters.job_type ?? ''}
          onChange={(e) => handleSelectChange('job_type', e.target.value)}
        >
          {JOB_TYPES.map((t) => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </Select>
      </div>

      <div>
        <label htmlFor="source-filter" className="mb-1.5 block text-xs font-medium text-foreground/70">
          Source
        </label>
        <Select
          id="source-filter"
          value={filters.source ?? ''}
          onChange={(e) => handleSelectChange('source', e.target.value)}
        >
          {SOURCES.map((s) => (
            <option key={s.value} value={s.value}>{s.label}</option>
          ))}
        </Select>
      </div>

      <button
        type="button"
        onClick={handleRemoteToggle}
        className={`flex w-full items-center justify-between rounded-lg border px-3 py-2.5 text-sm transition-colors ${
          filters.is_remote
            ? 'border-green-300 bg-green-50 text-green-700 dark:border-green-800 dark:bg-green-950 dark:text-green-400'
            : 'border-foreground/20 text-foreground/70 hover:bg-foreground/5'
        }`}
        aria-pressed={!!filters.is_remote}
        aria-label="Toggle remote only filter"
      >
        <span>Remote Only</span>
        <span className={`h-4 w-8 rounded-full transition-colors ${filters.is_remote ? 'bg-green-500' : 'bg-foreground/20'} relative`}>
          <span className={`absolute top-0.5 h-3 w-3 rounded-full bg-white transition-transform ${filters.is_remote ? 'translate-x-4' : 'translate-x-0.5'}`} />
        </span>
      </button>

      <div>
        <span className="mb-1.5 block text-xs font-medium text-foreground/70">Salary Range</span>
        <div className="flex items-center gap-2">
          <Input
            type="number"
            placeholder="Min"
            value={filters.salary_min ?? ''}
            onChange={(e) => handleSalaryChange('salary_min', e.target.value)}
            aria-label="Minimum salary"
          />
          <span className="text-foreground/40">-</span>
          <Input
            type="number"
            placeholder="Max"
            value={filters.salary_max ?? ''}
            onChange={(e) => handleSalaryChange('salary_max', e.target.value)}
            aria-label="Maximum salary"
          />
        </div>
      </div>

      {hasFilters && (
        <Button variant="ghost" size="sm" className="w-full" onClick={clearFilters}>
          <X className="h-3 w-3" />
          Clear Filters
        </Button>
      )}
    </div>
  );
}
