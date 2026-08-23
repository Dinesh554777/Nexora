import {
  AnalyticsResponse,
  ImplantMatchResponse,
  PatientMeasurementsRequest,
  SegmentImageResponse,
  APIError,
  DemoCasesListResponse,
  DemoReport,
  OAAssessmentResponse,
} from '@/types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class APIService {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      
      try {
        const errorData: APIError = await response.json();
        errorMessage = errorData.detail || errorMessage;
      } catch {
        // If parsing fails, use default error message
      }

      throw new Error(errorMessage);
    }

    return response.json();
  }

  async getAnalytics(): Promise<AnalyticsResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/analytics`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      return this.handleResponse<AnalyticsResponse>(response);
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(`Failed to fetch analytics: ${error.message}`);
      }
      throw new Error('Failed to fetch analytics: Unknown error');
    }
  }

  async matchImplant(measurements: PatientMeasurementsRequest): Promise<ImplantMatchResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/implant-match`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(measurements),
      });

      return this.handleResponse<ImplantMatchResponse>(response);
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(`Failed to match implant: ${error.message}`);
      }
      throw new Error('Failed to match implant: Unknown error');
    }
  }

  async healthCheck(): Promise<{ status: string; service: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      return this.handleResponse<{ status: string; service: string }>(response);
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(`Health check failed: ${error.message}`);
      }
      throw new Error('Health check failed: Unknown error');
    }
  }

  async segmentImage(formData: FormData): Promise<SegmentImageResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/segment`, {
        method: 'POST',
        body: formData,
      });

      return this.handleResponse<SegmentImageResponse>(response);
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(`Image analysis failed: ${error.message}`);
      }
      throw new Error('Image analysis failed: Unknown error');
    }
  }

  async getDemoCases(): Promise<DemoCasesListResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/demo-cases`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      return this.handleResponse<DemoCasesListResponse>(response);
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(`Failed to fetch demo cases: ${error.message}`);
      }
      throw new Error('Failed to fetch demo cases: Unknown error');
    }
  }

  async getDemoCase(caseId: string): Promise<DemoReport> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/demo-cases/${encodeURIComponent(caseId)}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      return this.handleResponse<DemoReport>(response);
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(`Failed to fetch demo case: ${error.message}`);
      }
      throw new Error('Failed to fetch demo case: Unknown error');
    }
  }

  async oaAssessment(formData: FormData): Promise<OAAssessmentResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/oa-assessment`, {
        method: 'POST',
        body: formData,
      });
      return this.handleResponse<OAAssessmentResponse>(response);
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(`OA assessment failed: ${error.message}`);
      }
      throw new Error('OA assessment failed: Unknown error');
    }
  }
}

// Export singleton instance
export const apiService = new APIService(API_BASE_URL);
