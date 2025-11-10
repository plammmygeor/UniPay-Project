import { useState } from 'react';
import { motion } from 'framer-motion';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { CreditCard, Banknote, QrCode, Wallet } from 'lucide-react';
import { walletAPI } from '@/lib/api';
import { toast } from 'sonner';
import { useCurrencyStore, formatCurrency, convertCurrency, convertToUSD } from '@/stores/currencyStore';

const MotionCard = motion.create(Card);

export default function TopupPage() {
  const [amount, setAmount] = useState('');
  const [selectedMethod, setSelectedMethod] = useState<'bank' | 'card' | 'qr'>('card');
  const queryClient = useQueryClient();
  const { selectedCurrency } = useCurrencyStore();

  const { data: walletData } = useQuery({
    queryKey: ['wallet'],
    queryFn: async () => {
      const response = await walletAPI.getWallet();
      return response.data.wallet;
    },
  });

  const topupMutation = useMutation({
    mutationFn: ({ amount, method }: { amount: number; method: string }) =>
      walletAPI.topup(amount, method),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['wallet'] });
      queryClient.invalidateQueries({ queryKey: ['all-transactions'] });
      queryClient.invalidateQueries({ queryKey: ['transaction-stats'] });
      toast.success(`Successfully added ${formatCurrency(variables.amount, selectedCurrency)} to your wallet!`);
      setAmount('');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Top-up failed');
    },
  });

  const handleTopup = () => {
    if (!amount || Number(amount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }
    const amountInUSD = convertToUSD(Number(amount), selectedCurrency);
    topupMutation.mutate({
      amount: amountInUSD,
      method: selectedMethod,
    });
  };

  const quickAmounts = [10, 25, 50, 100, 200];

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 },
  };

  return (
    <motion.div
      className="p-6 max-w-4xl mx-auto space-y-6"
      variants={containerVariants}
      initial="hidden"
      animate="show"
    >
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-600 to-indigo-600 bg-clip-text text-transparent">
          Top Up Wallet
        </h1>
        <p className="text-gray-600 mt-2">Add funds to your digital wallet</p>
      </div>

      <MotionCard variants={itemVariants} className="bg-gradient-to-br from-violet-50 to-indigo-50 dark:from-violet-950 dark:to-indigo-950">
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="p-4 bg-gradient-to-br from-violet-600 to-indigo-600 rounded-xl">
              <Wallet className="h-8 w-8 text-white" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Current Balance</p>
              <p className="text-3xl font-bold text-violet-600">
                {formatCurrency(walletData?.balance || 0, selectedCurrency)}
              </p>
            </div>
          </div>
        </CardContent>
      </MotionCard>

      <MotionCard variants={itemVariants}>
        <CardHeader>
          <CardTitle>Select Top-up Method</CardTitle>
          <CardDescription>Choose how you'd like to add funds</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              className={`p-6 rounded-lg border-2 transition-all hover:shadow-md ${
                selectedMethod === 'card'
                  ? 'border-violet-600 bg-violet-50 dark:bg-violet-950'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setSelectedMethod('card')}
            >
              <CreditCard className={`h-8 w-8 mb-3 mx-auto ${
                selectedMethod === 'card' ? 'text-violet-600' : 'text-gray-400'
              }`} />
              <p className="font-medium">Credit/Debit Card</p>
              <p className="text-sm text-gray-500 mt-1">Instant transfer</p>
            </button>

            <button
              className={`p-6 rounded-lg border-2 transition-all hover:shadow-md ${
                selectedMethod === 'bank'
                  ? 'border-violet-600 bg-violet-50 dark:bg-violet-950'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setSelectedMethod('bank')}
            >
              <Banknote className={`h-8 w-8 mb-3 mx-auto ${
                selectedMethod === 'bank' ? 'text-violet-600' : 'text-gray-400'
              }`} />
              <p className="font-medium">Bank Transfer</p>
              <p className="text-sm text-gray-500 mt-1">1-2 business days</p>
            </button>

            <button
              className={`p-6 rounded-lg border-2 transition-all hover:shadow-md ${
                selectedMethod === 'qr'
                  ? 'border-violet-600 bg-violet-50 dark:bg-violet-950'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setSelectedMethod('qr')}
            >
              <QrCode className={`h-8 w-8 mb-3 mx-auto ${
                selectedMethod === 'qr' ? 'text-violet-600' : 'text-gray-400'
              }`} />
              <p className="font-medium">QR Code</p>
              <p className="text-sm text-gray-500 mt-1">Scan to pay</p>
            </button>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="amount">Amount</Label>
              <Input
                id="amount"
                type="number"
                min="1"
                step="0.01"
                placeholder="Enter amount"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
              />
            </div>

            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">Quick amounts:</p>
              <div className="flex flex-wrap gap-2">
                {quickAmounts.map((quickAmount) => (
                  <Button
                    key={quickAmount}
                    variant="outline"
                    size="sm"
                    onClick={() => setAmount(convertCurrency(quickAmount, selectedCurrency).toString())}
                  >
                    {formatCurrency(quickAmount, selectedCurrency)}
                  </Button>
                ))}
              </div>
            </div>

            <Button
              className="w-full bg-gradient-to-r from-violet-600 to-indigo-600 text-lg py-6"
              onClick={handleTopup}
              disabled={topupMutation.isPending || !amount || Number(amount) <= 0}
            >
              {topupMutation.isPending ? 'Processing...' : `Top Up ${amount ? formatCurrency(convertToUSD(Number(amount), selectedCurrency), selectedCurrency) : formatCurrency(0, selectedCurrency)}`}
            </Button>

            <p className="text-sm text-gray-500 text-center">
              Funds will be added instantly to your wallet
            </p>
          </div>
        </CardContent>
      </MotionCard>

      <MotionCard variants={itemVariants} className="bg-blue-50 dark:bg-blue-950 border-blue-200">
        <CardContent className="pt-6">
          <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
            💡 Top-up Tips
          </h3>
          <ul className="space-y-2 text-sm text-blue-800 dark:text-blue-200">
            <li>• Minimum top-up amount: $1.00</li>
            <li>• Card payments are processed instantly</li>
            <li>• Bank transfers may take 1-2 business days</li>
            <li>• All transactions are secured with SSL encryption</li>
          </ul>
        </CardContent>
      </MotionCard>
    </motion.div>
  );
}
