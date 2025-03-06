import React, { useState, useEffect } from 'react';
import { 
  Box, 
  FormControl, 
  FormLabel, 
  Select, 
  Button, 
  Flex,
  Alert,
  AlertIcon,
  Text,
  Badge,
  Spinner,
  Tooltip,
  HStack,
  VStack,
  Divider,
  Heading,
  Card,
  CardHeader,
  CardBody
} from '@chakra-ui/react';
import axios from 'axios';

const DatabaseSelector = () => {
  const [loading, setLoading] = useState(true);
  const [switching, setSwitching] = useState(false);
  const [status, setStatus] = useState({});
  const [error, setError] = useState(null);
  const [selectedProvider, setSelectedProvider] = useState('');

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/settings/database/status');
      setStatus(response.data);
      setSelectedProvider(response.data.current_provider);
      setError(null);
    } catch (err) {
      setError('Error fetching database status: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleSwitch = async () => {
    if (selectedProvider === status.current_provider) return;
    
    setSwitching(true);
    try {
      await axios.post('/api/settings/database/switch', selectedProvider, {
        headers: {
          'Content-Type': 'text/plain'
        }
      });
      await fetchStatus();
      setError(null);
    } catch (err) {
      setError('Error switching database provider: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSwitching(false);
    }
  };

  const getProviderBadge = (provider) => {
    const isConnected = status[provider] === true;
    const isCurrent = status.current_provider === provider;
    
    return (
      <Badge 
        colorScheme={isConnected ? (isCurrent ? 'green' : 'blue') : 'gray'}
        variant={isCurrent ? 'solid' : 'outline'}
      >
        {isConnected ? (isCurrent ? 'Active' : 'Available') : 'Unavailable'}
      </Badge>
    );
  };

  const getResumeCount = (provider) => {
    if (!status.resume_counts || status.resume_counts[provider] === undefined) return '?';
    return status.resume_counts[provider];
  };

  return (
    <Card>
      <CardHeader>
        <Heading size="md">Database Provider</Heading>
      </CardHeader>
      <CardBody>
        <VStack spacing={4} align="stretch">
          {error && (
            <Alert status="error">
              <AlertIcon />
              {error}
            </Alert>
          )}
          
          {loading ? (
            <Flex justify="center" p={4}>
              <Spinner />
            </Flex>
          ) : (
            <>
              <FormControl>
                <FormLabel>Select Database Provider</FormLabel>
                <Select 
                  value={selectedProvider}
                  onChange={(e) => setSelectedProvider(e.target.value)}
                  isDisabled={switching}
                >
                  <option value="postgres">
                    PostgreSQL (Local)
                  </option>
                  <option value="supabase">
                    Supabase (Cloud)
                  </option>
                </Select>
              </FormControl>
              
              <Divider />
              
              <Heading size="xs">Provider Status</Heading>
              
              <HStack justifyContent="space-between">
                <Text>PostgreSQL:</Text>
                <HStack>
                  {getProviderBadge('postgres')}
                  <Tooltip label="Number of resumes">
                    <Badge colorScheme="purple" variant="outline">
                      {getResumeCount('postgres')} resumes
                    </Badge>
                  </Tooltip>
                </HStack>
              </HStack>
              
              <HStack justifyContent="space-between">
                <Text>Supabase:</Text>
                <HStack>
                  {getProviderBadge('supabase')}
                  <Tooltip label="Number of resumes">
                    <Badge colorScheme="purple" variant="outline">
                      {getResumeCount('supabase')} resumes
                    </Badge>
                  </Tooltip>
                </HStack>
              </HStack>
              
              <Divider />
              
              <Button
                colorScheme="blue"
                onClick={handleSwitch}
                isLoading={switching}
                isDisabled={selectedProvider === status.current_provider}
              >
                Switch Provider
              </Button>
            </>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
};

export default DatabaseSelector;