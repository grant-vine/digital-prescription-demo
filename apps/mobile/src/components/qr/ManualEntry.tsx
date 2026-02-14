import { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Clipboard,
} from 'react-native';

export interface VerifiableCredential {
  '@context'?: string[];
  type: string[];
  issuer: string;
  credentialSubject: {
    prescriptionId: string;
    patientName: string;
    medications: Array<{
      name: string;
      dosage: string;
      frequency: string;
    }>;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export interface ManualEntryProps {
  onCredentialParsed: (credential: VerifiableCredential) => void;
  onError?: (error: Error) => void;
}

export default function ManualEntry({
  onCredentialParsed,
  onError,
}: ManualEntryProps) {
  const [jsonInput, setJsonInput] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handlePaste = async () => {
    try {
      const content = await Clipboard.getString();
      setJsonInput(content);
      setError(null);
    } catch (err) {
      Alert.alert('Error', 'Failed to paste from clipboard');
    }
  };

  const validateAndSubmit = () => {
    setError(null);

    if (!jsonInput.trim()) {
      const err = new Error('Please enter prescription data');
      setError(err.message);
      return;
    }

    try {
      const credential = JSON.parse(jsonInput);

      if (!credential.type || !Array.isArray(credential.type)) {
        throw Object.assign(new Error('Invalid credential type'), {
          name: 'INVALID_CREDENTIAL_TYPE',
        });
      }

      if (!credential.type.includes('VerifiableCredential')) {
        throw Object.assign(new Error('This is not a valid prescription'), {
          name: 'INVALID_CREDENTIAL_TYPE',
        });
      }

      if (!credential.issuer) {
        throw Object.assign(new Error('Incomplete prescription data'), {
          name: 'MISSING_FIELD',
          field: 'issuer',
        });
      }

      if (!credential.credentialSubject) {
        throw Object.assign(new Error('Incomplete prescription data'), {
          name: 'MISSING_FIELD',
          field: 'credentialSubject',
        });
      }

      onCredentialParsed(credential as VerifiableCredential);
    } catch (err) {
      let errorObj: Error;
      
      if (err instanceof SyntaxError) {
        errorObj = new Error('Invalid JSON format');
        errorObj.name = 'INVALID_JSON';
      } else {
        errorObj = err as Error;
      }
      
      setError(errorObj.message);
      onError?.(errorObj);
    }
  };

  return (
    <View style={styles.container} testID="manual-entry-root">
      <Text style={styles.title}>Manual Code Entry</Text>
      <Text style={styles.subtitle}>
        Paste the prescription data JSON string below if camera scanning is unavailable.
      </Text>

      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          multiline
          placeholder='{ "@context": [...], "type": ... }'
          placeholderTextColor="#9CA3AF"
          value={jsonInput}
          onChangeText={(text) => {
            setJsonInput(text);
            setError(null);
          }}
          testID="json-input"
        />
        <TouchableOpacity
          style={styles.pasteButton}
          onPress={handlePaste}
          testID="paste-button"
        >
          <Text style={styles.pasteButtonText}>Paste</Text>
        </TouchableOpacity>
      </View>

      {error && (
        <Text style={styles.errorText} testID="error-message">
          {error}
        </Text>
      )}

      <TouchableOpacity
        style={[
          styles.submitButton,
          !jsonInput.trim() && styles.submitButtonDisabled,
        ]}
        onPress={validateAndSubmit}
        disabled={!jsonInput.trim()}
        testID="submit-button"
      >
        <Text style={styles.submitButtonText}>Process Prescription</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 20,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    width: '100%',
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1F2937',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 16,
    textAlign: 'center',
  },
  inputContainer: {
    position: 'relative',
    marginBottom: 16,
  },
  input: {
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    padding: 12,
    height: 120,
    textAlignVertical: 'top',
    fontSize: 14,
    color: '#1F2937',
    backgroundColor: '#F9FAFB',
  },
  pasteButton: {
    position: 'absolute',
    right: 8,
    top: 8,
    backgroundColor: '#E5E7EB',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  pasteButtonText: {
    fontSize: 12,
    color: '#374151',
    fontWeight: '500',
  },
  errorText: {
    color: '#DC2626',
    fontSize: 14,
    marginBottom: 16,
    textAlign: 'center',
  },
  submitButton: {
    backgroundColor: '#2563EB',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  submitButtonDisabled: {
    backgroundColor: '#93C5FD',
  },
  submitButtonText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: 16,
  },
});
