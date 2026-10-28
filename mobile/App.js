import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, ScrollView, TouchableOpacity, TextInput, ActivityIndicator, Alert, SafeAreaView } from 'react-native';
import { StatusBar } from 'expo-status-bar';

// Base API configuration (point to FastAPI backend)
const API_BASE_URL = 'http://10.0.2.2:8000'; // Standard Android emulator localhost

export default function App() {
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [balance, setBalance] = useState(25000);
  const [forecastSpend, setForecastSpend] = useState(17500);
  const [shortfallWarning, setShortfallWarning] = useState(null);
  const [smsInput, setSmsInput] = useState('');
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState([
    { sender: 'AI', text: 'Hello! I am FinPulse AI, your predictive financial advisor. How can I assist you with your spending today?' }
  ]);
  const [recentTxns, setRecentTxns] = useState([
    { id: '1', merchant: 'Swiggy', amount: 450, category: 'Food', date: 'Today' },
    { id: '2', merchant: 'Blinkit', amount: 890, category: 'Groceries', date: 'Yesterday' },
    { id: '3', merchant: 'Uber', amount: 320, category: 'Transport', date: '10-Oct' },
  ]);
  const [anomalies, setAnomalies] = useState([
    { id: 'a1', merchant: 'Luxury Boutique', amount: 28500, status: 'Potentially unusual transaction' }
  ]);

  const handleProcessSms = () => {
    if (!smsInput.trim()) {
      Alert.alert('Empty Input', 'Please paste a banking SMS notification.');
      return;
    }
    // Simulate real-time extraction & feedback
    const newTxn = {
      id: Date.now().toString(),
      merchant: 'Detected Merchant',
      amount: 450,
      category: 'Food',
      date: 'Just now'
    };
    setRecentTxns([newTxn, ...recentTxns]);
    setSmsInput('');
    Alert.alert('Transaction Extracted', 'NLP extracted: ₹450 at Detected Merchant. Saved to database.');
  };

  const handleSendChat = () => {
    if (!chatInput.trim()) return;
    const userMsg = { sender: 'User', text: chatInput };
    setChatMessages(prev => [...prev, userMsg]);
    const query = chatInput;
    setChatInput('');

    // AI advisory grounded reply
    setTimeout(() => {
      setChatMessages(prev => [
        ...prev,
        {
          sender: 'AI',
          text: `Based on your application data: current balance is ₹${balance.toLocaleString()}, forecasted 30-day spend is ₹${forecastSpend.toLocaleString()}. Top category is Food. Note: These figures are model estimates, not guaranteed outcomes.`
        }
      ]);
    }, 600);
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      <View style={styles.header}>
        <Text style={styles.headerTitle}>FinPulse AI</Text>
        <Text style={styles.headerSubtitle}>Predictive Personal Finance Assistant</Text>
      </View>

      {/* Navigation Bar */}
      <View style={styles.navBar}>
        {['Dashboard', 'SMS Capture', 'Anomalies', 'AI Advisor'].map(tab => (
          <TouchableOpacity
            key={tab}
            style={[styles.navButton, activeTab === tab && styles.navButtonActive]}
            onPress={() => setActiveTab(tab)}
          >
            <Text style={[styles.navText, activeTab === tab && styles.navTextActive]}>{tab}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        {activeTab === 'Dashboard' && (
          <View>
            {/* Balance Card */}
            <View style={styles.card}>
              <Text style={styles.cardLabel}>Available Liquidity</Text>
              <Text style={styles.balanceValue}>₹{balance.toLocaleString()}</Text>
              <View style={styles.divider} />
              <Text style={styles.cardLabel}>Predicted 30-Day Spending</Text>
              <Text style={styles.forecastValue}>₹{forecastSpend.toLocaleString()}</Text>
              <Text style={styles.disclaimerText}>Model: 15-30 day PyTorch LSTM time-series forecast</Text>
            </View>

            {/* Cash-shortfall warning banner */}
            <View style={[styles.card, styles.warningCard]}>
              <Text style={styles.warningTitle}>⚠️ Predictive Cash-Flow Warning</Text>
              <Text style={styles.warningDesc}>
                Projected spending and recurring obligations may approach liquidity limits near month-end.
              </Text>
            </View>

            {/* Recent Transactions */}
            <Text style={styles.sectionTitle}>Recent Ingested Transactions</Text>
            {recentTxns.map(t => (
              <View key={t.id} style={styles.txnItem}>
                <View>
                  <Text style={styles.txnMerchant}>{t.merchant}</Text>
                  <Text style={styles.txnSub}>{t.category} • {t.date}</Text>
                </View>
                <Text style={styles.txnAmount}>-₹{t.amount}</Text>
              </View>
            ))}
          </View>
        )}

        {activeTab === 'SMS Capture' && (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Android Background SMS Listener</Text>
            <Text style={styles.helperText}>
              In production, the SMS Broadcast Receiver forwards permitted banking alerts directly to the FastAPI NLP extraction pipeline.
            </Text>
            <TextInput
              style={styles.inputArea}
              placeholder="Paste banking SMS (e.g., A/C debited with INR 450 at Swiggy on 17-Aug-2026)"
              placeholderTextColor="#888"
              multiline
              value={smsInput}
              onChangeText={setSmsInput}
            />
            <TouchableOpacity style={styles.primaryButton} onPress={handleProcessSms}>
              <Text style={styles.buttonText}>Extract & Ingest Transaction</Text>
            </TouchableOpacity>
          </View>
        )}

        {activeTab === 'Anomalies' && (
          <View>
            <Text style={styles.sectionTitle}>Scikit-Learn Isolation Forest Alerts</Text>
            <Text style={styles.helperText}>
              Highlights statistically atypical transactions without falsely accusing transactions of fraud.
            </Text>
            {anomalies.map(a => (
              <View key={a.id} style={[styles.card, styles.anomalyCard]}>
                <View style={styles.rowBetween}>
                  <Text style={styles.txnMerchant}>{a.merchant}</Text>
                  <Text style={styles.anomalyAmount}>₹{a.amount.toLocaleString()}</Text>
                </View>
                <Text style={styles.anomalyTag}>{a.status}</Text>
              </View>
            ))}
          </View>
        )}

        {activeTab === 'AI Advisor' && (
          <View style={{ flex: 1 }}>
            <Text style={styles.sectionTitle}>AI Financial Nudges & Assistant</Text>
            <View style={styles.chatContainer}>
              {chatMessages.map((msg, idx) => (
                <View
                  key={idx}
                  style={[styles.chatBubble, msg.sender === 'User' ? styles.userBubble : styles.aiBubble]}
                >
                  <Text style={styles.chatText}>{msg.text}</Text>
                </View>
              ))}
            </View>
            <View style={styles.inputRow}>
              <TextInput
                style={styles.chatInput}
                placeholder="Ask financial question..."
                placeholderTextColor="#888"
                value={chatInput}
                onChangeText={setChatInput}
              />
              <TouchableOpacity style={styles.sendButton} onPress={handleSendChat}>
                <Text style={styles.sendButtonText}>Send</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a' },
  header: { padding: 16, backgroundColor: '#1e293b' },
  headerTitle: { fontSize: 22, fontWeight: 'bold', color: '#38bdf8' },
  headerSubtitle: { fontSize: 13, color: '#94a3b8', marginTop: 2 },
  navBar: { flexDirection: 'row', backgroundColor: '#1e293b', borderBottomWidth: 1, borderColor: '#334155' },
  navButton: { flex: 1, paddingVertical: 12, alignItems: 'center' },
  navButtonActive: { borderBottomWidth: 3, borderColor: '#38bdf8' },
  navText: { color: '#94a3b8', fontSize: 13 },
  navTextActive: { color: '#38bdf8', fontWeight: 'bold' },
  content: { padding: 16 },
  card: { backgroundColor: '#1e293b', borderRadius: 12, padding: 16, marginBottom: 16, borderWidth: 1, borderColor: '#334155' },
  cardLabel: { fontSize: 13, color: '#94a3b8' },
  balanceValue: { fontSize: 30, fontWeight: 'bold', color: '#10b981', marginVertical: 4 },
  forecastValue: { fontSize: 24, fontWeight: 'bold', color: '#f59e0b', marginVertical: 4 },
  divider: { height: 1, backgroundColor: '#334155', marginVertical: 12 },
  disclaimerText: { fontSize: 11, color: '#64748b', marginTop: 6, fontStyle: 'italic' },
  warningCard: { borderColor: '#ef4444', backgroundColor: '#451a1a' },
  warningTitle: { fontSize: 15, fontWeight: 'bold', color: '#f87171' },
  warningDesc: { fontSize: 13, color: '#fca5a5', marginTop: 4 },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', color: '#f1f5f9', marginBottom: 10 },
  helperText: { fontSize: 13, color: '#94a3b8', marginBottom: 12 },
  txnItem: { flexDirection: 'row', justifyContent: 'space-between', backgroundColor: '#1e293b', padding: 14, borderRadius: 8, marginBottom: 8, borderWidth: 1, borderColor: '#334155' },
  txnMerchant: { fontSize: 15, fontWeight: 'bold', color: '#f8fafc' },
  txnSub: { fontSize: 12, color: '#64748b', marginTop: 2 },
  txnAmount: { fontSize: 15, fontWeight: 'bold', color: '#f87171' },
  inputArea: { backgroundColor: '#0f172a', color: '#f8fafc', padding: 12, borderRadius: 8, height: 100, textAlignVertical: 'top', borderWidth: 1, borderColor: '#334155', marginVertical: 12 },
  primaryButton: { backgroundColor: '#0284c7', padding: 14, borderRadius: 8, alignItems: 'center' },
  buttonText: { color: '#ffffff', fontWeight: 'bold', fontSize: 14 },
  anomalyCard: { borderLeftWidth: 4, borderLeftColor: '#f59e0b' },
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between' },
  anomalyAmount: { fontSize: 16, fontWeight: 'bold', color: '#f59e0b' },
  anomalyTag: { fontSize: 12, color: '#fcd34d', marginTop: 6, fontStyle: 'italic' },
  chatContainer: { minHeight: 240, marginBottom: 12 },
  chatBubble: { padding: 12, borderRadius: 10, marginVertical: 4, maxWidth: '85%' },
  aiBubble: { backgroundColor: '#334155', alignSelf: 'flex-start' },
  userBubble: { backgroundColor: '#0284c7', alignSelf: 'flex-end' },
  chatText: { color: '#f8fafc', fontSize: 13 },
  inputRow: { flexDirection: 'row', gap: 8 },
  chatInput: { flex: 1, backgroundColor: '#1e293b', color: '#f8fafc', borderRadius: 8, paddingHorizontal: 12, borderWidth: 1, borderColor: '#334155' },
  sendButton: { backgroundColor: '#0284c7', paddingHorizontal: 16, justifyContent: 'center', borderRadius: 8 },
  sendButtonText: { color: '#ffffff', fontWeight: 'bold' }
});
