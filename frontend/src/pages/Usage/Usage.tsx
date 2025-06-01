import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  InputAdornment,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Alert,
  CircularProgress,
  useTheme,
  LinearProgress,
  Avatar,
} from '@mui/material';
import {
  Search as SearchIcon,
  Phone as PhoneIcon,
  AccessTime as AccessTimeIcon,
  TrendingUp as TrendingUpIcon,
  CallMade as CallMadeIcon,
  CallReceived as CallReceivedIcon,
} from '@mui/icons-material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { useQuery } from 'react-query';
import { usageAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

interface UsageRecord {
  id: number;
  call_id: string;
  start_time: string;
  end_time?: string;
  duration?: number;
  status: string;
  caller_number: string;
  destination_number: string;
  call_type: string;
  call_summary?: string;
  user?: {
    id: number;
    email: string;
    full_name: string;
  };
}

interface UsageStats {
  total_calls: number;
  total_minutes: number;
  completed_calls: number;
  failed_calls: number;
  average_duration: number;
  usage_percentage: number;
}

const Usage: React.FC = () => {
  const theme = useTheme();
  const { user } = useAuth();
  const isAdmin = user?.is_superuser;
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [dateRange, setDateRange] = useState({
    start: '',
    end: '',
  });

  const { data: usageRecords, isLoading: recordsLoading, error: recordsError } = useQuery(
    ['usage', searchTerm, statusFilter, typeFilter, dateRange],
    () => {
      const params: any = {};
      if (searchTerm) params.user_email = searchTerm;
      if (statusFilter) params.call_status = statusFilter;
      if (typeFilter) params.call_type = typeFilter;
      if (dateRange.start) params.start_date = dateRange.start;
      if (dateRange.end) params.end_date = dateRange.end;
      
      return isAdmin ? usageAPI.getUsage(params) : usageAPI.getMyUsage(params);
    },
    {
      keepPreviousData: true,
    }
  );

  const { data: analytics, isLoading: analyticsLoading } = useQuery(
    ['usage-analytics', dateRange],
    () => {
      const params: any = {};
      if (dateRange.start) params.start_date = dateRange.start;
      if (dateRange.end) params.end_date = dateRange.end;
      
      return isAdmin ? usageAPI.getAnalytics(params) : usageAPI.getMyUsage(params);
    }
  );

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'connected':
        return 'info';
      case 'initiated':
        return 'warning';
      default:
        return 'default';
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '0s';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return minutes > 0 ? `${minutes}m ${remainingSeconds}s` : `${remainingSeconds}s`;
  };

  const columns: GridColDef[] = [
    {
      field: 'call_type',
      headerName: 'Type',
      width: 80,
      renderCell: (params) => (
        <Avatar
          sx={{
            width: 32,
            height: 32,
            bgcolor: params.value === 'inbound' ? theme.palette.success.main : theme.palette.primary.main,
          }}
        >
          {params.value === 'inbound' ? <CallReceivedIcon /> : <CallMadeIcon />}
        </Avatar>
      ),
    },
    {
      field: 'caller_number',
      headerName: 'From',
      flex: 1,
      minWidth: 120,
    },
    {
      field: 'destination_number',
      headerName: 'To',
      flex: 1,
      minWidth: 120,
    },
    ...(isAdmin ? [{
      field: 'user',
      headerName: 'User',
      flex: 1,
      minWidth: 150,
      renderCell: (params: any) => params.value?.full_name || params.value?.email || 'Unknown',
    }] : []),
    {
      field: 'duration',
      headerName: 'Duration',
      width: 100,
      renderCell: (params) => formatDuration(params.value),
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value}
          color={getStatusColor(params.value) as any}
          size="small"
        />
      ),
    },
    {
      field: 'start_time',
      headerName: 'Started',
      width: 160,
      renderCell: (params) => new Date(params.value).toLocaleString(),
    },
  ];

  if (recordsError) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        Failed to load usage data. Please try again.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" fontWeight="bold" sx={{ mb: 4 }}>
        {isAdmin ? 'Usage Analytics' : 'My Usage'}
      </Typography>

      {/* Stats Cards */}
      {analytics && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Avatar sx={{ bgcolor: theme.palette.primary.main, mr: 2 }}>
                    <PhoneIcon />
                  </Avatar>
                  <Box>
                    <Typography color="text.secondary" variant="body2">
                      Total Calls
                    </Typography>
                    <Typography variant="h4" fontWeight="bold">
                      {analytics.total_calls || 0}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Avatar sx={{ bgcolor: theme.palette.success.main, mr: 2 }}>
                    <AccessTimeIcon />
                  </Avatar>
                  <Box>
                    <Typography color="text.secondary" variant="body2">
                      Total Minutes
                    </Typography>
                    <Typography variant="h4" fontWeight="bold">
                      {Math.round(analytics.total_minutes || 0)}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Avatar sx={{ bgcolor: theme.palette.warning.main, mr: 2 }}>
                    <TrendingUpIcon />
                  </Avatar>
                  <Box>
                    <Typography color="text.secondary" variant="body2">
                      Success Rate
                    </Typography>
                    <Typography variant="h4" fontWeight="bold">
                      {analytics.total_calls > 0 
                        ? Math.round((analytics.completed_calls / analytics.total_calls) * 100)
                        : 0}%
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Avatar sx={{ bgcolor: theme.palette.secondary.main, mr: 2 }}>
                    <AccessTimeIcon />
                  </Avatar>
                  <Box>
                    <Typography color="text.secondary" variant="body2">
                      Avg Duration
                    </Typography>
                    <Typography variant="h4" fontWeight="bold">
                      {formatDuration(analytics.average_duration)}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Usage Progress (for non-admin users) */}
      {!isAdmin && analytics?.usage_percentage !== undefined && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
              Plan Usage
            </Typography>
            <Box sx={{ mb: 1 }}>
              <Typography variant="body2" color="text.secondary">
                {analytics.usage_percentage}% of plan limit used
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={Math.min(analytics.usage_percentage, 100)}
              sx={{ height: 8, borderRadius: 4 }}
              color={analytics.usage_percentage > 90 ? 'error' : analytics.usage_percentage > 75 ? 'warning' : 'primary'}
            />
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                placeholder={isAdmin ? "Search by user email..." : "Search calls..."}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  label="Status"
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="failed">Failed</MenuItem>
                  <MenuItem value="connected">Connected</MenuItem>
                  <MenuItem value="initiated">Initiated</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth>
                <InputLabel>Type</InputLabel>
                <Select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  label="Type"
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="inbound">Inbound</MenuItem>
                  <MenuItem value="outbound">Outbound</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={2.5}>
              <TextField
                fullWidth
                label="Start Date"
                type="date"
                value={dateRange.start}
                onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2.5}>
              <TextField
                fullWidth
                label="End Date"
                type="date"
                value={dateRange.end}
                onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Usage Records Table */}
      <Card>
        <Box sx={{ height: 600, width: '100%' }}>
          <DataGrid
            rows={usageRecords || []}
            columns={columns}
            loading={recordsLoading}
            pageSizeOptions={[10, 25, 50]}
            initialState={{
              pagination: {
                paginationModel: { pageSize: 25 },
              },
            }}
            disableRowSelectionOnClick
          />
        </Box>
      </Card>
    </Box>
  );
};

export default Usage;
